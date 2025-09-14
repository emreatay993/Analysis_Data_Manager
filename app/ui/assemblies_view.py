from PyQt5 import QtWidgets, QtCore
from app.data import store
from app.assembly.contact_detection import compute_contacts, compute_contacts_occ
from app.assembly.viewer import AssemblyViewer
from app.assembly.mesh_utils import shape_to_mesh
from app.assembly.step_loader import load_shape_for_member


class AssembliesView(QtWidgets.QWidget):
    def __init__(self, project: str, main_window: QtWidgets.QMainWindow | None = None):
        super().__init__()
        self._project = project
        self._main_window = main_window
        self._dock_widget: QtWidgets.QDockWidget | None = None
        self._applied_initial_dock_size = False
        self._setup_ui()
        # Create viewer dock in a sensible default position/size
        if self._main_window is not None:
            self._create_viewer_dock(area=QtCore.Qt.TopDockWidgetArea)
            # Defer sizing until window is shown to compute correct height
            try:
                QtCore.QTimer.singleShot(0, self._set_initial_dock_size)
            except Exception:
                pass
            try:
                self._main_window.installEventFilter(self)
            except Exception:
                pass
        self.refresh()

    def set_project(self, project: str):
        self._project = project
        self.refresh()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        actions = QtWidgets.QHBoxLayout()
        self.btn_new = QtWidgets.QPushButton("New Assembly")
        self.btn_add_member = QtWidgets.QPushButton("Add Member")
        self.btn_contacts = QtWidgets.QPushButton("Compute Contacts (stub)")
        self.btn_contacts_occ = QtWidgets.QPushButton("Compute Contacts (OCC)")
        self.clearance_spin = QtWidgets.QDoubleSpinBox(); self.clearance_spin.setRange(0.1, 1000.0); self.clearance_spin.setValue(5.0); self.clearance_spin.setSuffix(" mm max clearance")
        actions.addWidget(self.btn_new)
        actions.addWidget(self.btn_add_member)
        actions.addWidget(self.btn_contacts)
        actions.addWidget(self.btn_contacts_occ)
        actions.addWidget(self.clearance_spin)

        self.assemblies = QtWidgets.QComboBox()
        self.members = QtWidgets.QTableWidget()
        self.members.setColumnCount(3)
        self.members.setHorizontalHeaderLabels(["Part", "Rev", "Included"])
        self.members.horizontalHeader().setStretchLastSection(True)

        self.viewer = AssemblyViewer()
        self.viewer.setMinimumHeight(300)

        self.contacts = QtWidgets.QTableWidget()
        self.contacts.setColumnCount(6)
        self.contacts.setHorizontalHeaderLabels(["A Part","A Rev","B Part","B Rev","Relation","Min Gap (mm)"])
        self.contacts.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(actions)
        layout.addWidget(QtWidgets.QLabel("Assembly:"))
        layout.addWidget(self.assemblies)

        main_split = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        main_split.setChildrenCollapsible(False)

        members_container = QtWidgets.QWidget(); members_layout = QtWidgets.QVBoxLayout(members_container); members_layout.setContentsMargins(0,0,0,0); members_layout.addWidget(QtWidgets.QLabel("Members:")); members_layout.addWidget(self.members)
        bottom_split = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        bottom_split.setChildrenCollapsible(False)
        bottom_contacts_container = QtWidgets.QWidget(); bottom_contacts_layout = QtWidgets.QVBoxLayout(bottom_contacts_container); bottom_contacts_layout.setContentsMargins(0,0,0,0); bottom_contacts_layout.addWidget(QtWidgets.QLabel("Contacts:")); bottom_contacts_layout.addWidget(self.contacts)
        bottom_split.addWidget(bottom_contacts_container)
        bottom_split.setStretchFactor(0, 1)

        main_split.addWidget(members_container)
        main_split.addWidget(bottom_split)
        main_split.setStretchFactor(0, 2)
        main_split.setStretchFactor(1, 3)

        layout.addWidget(main_split)

        self.btn_new.clicked.connect(self.on_new)
        self.btn_add_member.clicked.connect(self.on_add_member)
        self.btn_contacts.clicked.connect(self.on_contacts)
        self.btn_contacts_occ.clicked.connect(self.on_contacts_occ)
        self.assemblies.currentTextChanged.connect(self.refresh_members)
        self.contacts.itemSelectionChanged.connect(self.on_contact_selected)

    def _create_viewer_dock(self, area: QtCore.Qt.DockWidgetArea | None = None, floating: bool | None = None, geometry: QtCore.QByteArray | None = None):
        if self._main_window is None or self._dock_widget is not None:
            return
        dock = QtWidgets.QDockWidget("3D Viewer", self._main_window)
        dock.setObjectName("Dock3DViewer")
        dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        dock.setMinimumSize(400, 300)
        dock.setWidget(self.viewer)
        self._main_window.addDockWidget(area or QtCore.Qt.TopDockWidgetArea, dock)
        # Connect signals to manage floating window flags
        dock.topLevelChanged.connect(self._on_dock_top_level_changed)
        self._dock_widget = dock
        # Apply floating/geometry if explicitly requested by caller
        try:
            if floating is True:
                dock.setFloating(True)
                if isinstance(geometry, (bytes, bytearray, QtCore.QByteArray)) and len(geometry) > 0:
                    try:
                        dock.restoreGeometry(geometry)
                    except Exception:
                        pass
                else:
                    dock.resize(900, 700)
                self._apply_floating_window_flags()
        except Exception:
            pass

    def _on_dock_top_level_changed(self, floating: bool):
        # Ensure floating dock can be maximized and has sensible size
        if self._dock_widget is None:
            return
        if floating:
            self._apply_floating_window_flags()
            if self._dock_widget.width() < 400 or self._dock_widget.height() < 300:
                try:
                    self._dock_widget.resize(max(900, self._dock_widget.width()), max(700, self._dock_widget.height()))
                except Exception:
                    pass
        # No persistence needed

    def _apply_floating_window_flags(self):
        try:
            if self._dock_widget is None:
                return
            if not self._dock_widget.isFloating():
                return
            # Enable standard window behavior including maximize when floating
            self._dock_widget.setWindowFlag(QtCore.Qt.Window, True)
            self._dock_widget.setWindowFlag(QtCore.Qt.WindowMinimizeButtonHint, True)
            self._dock_widget.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
            self._dock_widget.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, True)
            self._dock_widget.show()
        except Exception:
            pass

    def _set_initial_dock_size(self):
        # Make the dock consume a sensible portion of the window height initially
        if self._dock_widget is None or self._main_window is None:
            return
        try:
            target_height = max(800, int(self._main_window.height() * 0.8))
            self._main_window.resizeDocks([self._dock_widget], [target_height], QtCore.Qt.Vertical)
        except Exception:
            try:
                # Fallback: direct resize
                self._dock_widget.resize(self._dock_widget.width(), max(800, int(self._main_window.height() * 0.8)))
            except Exception:
                pass

    def eventFilter(self, obj, event):
        try:
            if obj is self._main_window and not self._applied_initial_dock_size and event is not None:
                et = int(getattr(event, 'type', lambda: -1)())
                # QEvent.Show = 17, QEvent.Resize = 12
                if et in (12, 17):
                    # Wait until window is at its final (likely maximized) size
                    try:
                        wh = self._main_window.windowHandle()
                    except Exception:
                        wh = None
                    screen = wh.screen() if wh is not None else QtWidgets.QApplication.primaryScreen()
                    avail_h = screen.availableGeometry().height() if screen is not None else 0
                    if self._main_window.isVisible() and self._main_window.height() > 0:
                        if avail_h <= 0 or self._main_window.height() >= int(avail_h * 0.6):
                            self._set_initial_dock_size()
                            self._applied_initial_dock_size = True
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def refresh(self):
        store.seed_tables(self._project)
        rows = [r for r in store.read_all(self._project, "assemblies.csv") if r.get("project") == self._project]
        cur = self.assemblies.currentText()
        self.assemblies.blockSignals(True)
        self.assemblies.clear()
        for r in rows:
            self.assemblies.addItem(r.get("assembly_id", ""))
        idx = max(0, self.assemblies.findText(cur))
        self.assemblies.setCurrentIndex(idx)
        self.assemblies.blockSignals(False)
        self.refresh_members()

    def refresh_members(self):
        aid = self.assemblies.currentText()
        self.viewer.clear()
        if not aid:
            self.members.setRowCount(0)
            self.contacts.setRowCount(0)
            return
        m = [r for r in store.read_all(self._project, "assembly_members.csv") if r.get("project") == self._project and r.get("assembly_id") == aid and (r.get("included","true") or "").lower()=="true"]
        self.members.setRowCount(len(m))
        for i, r in enumerate(m):
            vals = [r.get("part_base",""), r.get("rev_index",""), r.get("included","true")]
            for c, v in enumerate(vals):
                self.members.setItem(i, c, QtWidgets.QTableWidgetItem(v))
            # Load shape and show in viewer
            try:
                part = r.get("part_base","")
                rev = int(r.get("rev_index","0") or 0)
                shape = load_shape_for_member(self._project, part, rev)
                mode = getattr(self.viewer, '_mode', '')
                if mode == 'occt' and shape is not None:
                    self.viewer.add_occ_shape(f"{part}_{rev}", shape)
                else:
                    verts, faces = shape_to_mesh(shape)
                    if getattr(verts, 'size', 0) and getattr(faces, 'size', 0):
                        self.viewer.add_mesh(f"{part}_{rev}", verts, faces)
            except Exception:
                pass
        # Load last contacts if any
        cts = [c for c in store.read_all(self._project, "contacts.csv") if c.get("project") == self._project and c.get("assembly_id") == aid]
        self.contacts.setRowCount(len(cts))
        for i, c in enumerate(cts):
            vals = [c.get("a_part",""), c.get("a_rev",""), c.get("b_part",""), c.get("b_rev",""), c.get("relation",""), c.get("min_gap_mm","")]
            for j, v in enumerate(vals):
                self.contacts.setItem(i, j, QtWidgets.QTableWidgetItem(v))

    def on_new(self):
        aid, ok = QtWidgets.QInputDialog.getText(self, "New Assembly", "Assembly ID:")
        if not ok or not aid.strip():
            return
        from time import strftime
        store.append_row(self._project, "assemblies.csv", {
            "project": self._project,
            "assembly_id": aid.strip(),
            "name": aid.strip(),
            "created_by": "",
            "created_at": strftime("%Y-%m-%d %H:%M:%S"),
            "note": "",
        })
        self.refresh()

    def on_add_member(self):
        aid = self.assemblies.currentText()
        if not aid:
            QtWidgets.QMessageBox.information(self, "Select", "Create/select an assembly first.")
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Add Member")
        form = QtWidgets.QFormLayout(dlg)
        part = QtWidgets.QLineEdit(); rev = QtWidgets.QSpinBox(); rev.setRange(1,999)
        form.addRow("Part base:", part)
        form.addRow("Revision index:", rev)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        store.append_row(self._project, "assembly_members.csv", {
            "project": self._project,
            "assembly_id": aid,
            "part_base": part.text().strip(),
            "rev_index": int(rev.value()),
            "included": "true",
        })
        self.refresh_members()

    def _gather_members(self):
        aid = self.assemblies.currentText()
        if not aid:
            return aid, []
        m = [r for r in store.read_all(self._project, "assembly_members.csv") if r.get("project") == self._project and r.get("assembly_id") == aid and (r.get("included","true") or "").lower()=="true"]
        members = [(r.get("part_base",""), int(r.get("rev_index","0") or 0)) for r in m]
        return aid, members

    def on_contacts(self):
        aid, members = self._gather_members()
        if not aid or not members:
            return
        contacts = compute_contacts(self._project, aid, members, clearance_max_mm=self.clearance_spin.value())
        allc = [c for c in store.read_all(self._project, "contacts.csv") if not (c.get("project") == self._project and c.get("assembly_id") == aid)]
        allc.extend(contacts)
        store.write_rows(self._project, "contacts.csv", allc)
        self.refresh_members()

    def on_contacts_occ(self):
        aid, members = self._gather_members()
        if not aid or not members:
            return
        contacts = compute_contacts_occ(self._project, aid, members, clearance_max_mm=self.clearance_spin.value())
        allc = [c for c in store.read_all(self._project, "contacts.csv") if not (c.get("project") == self._project and c.get("assembly_id") == aid)]
        allc.extend(contacts)
        store.write_rows(self._project, "contacts.csv", allc)
        self.refresh_members()

    def on_contact_selected(self):
        row = self.contacts.currentRow()
        if row < 0:
            return
        a = self.contacts.item(row, 0).text()
        a_rev = self.contacts.item(row, 1).text()
        b = self.contacts.item(row, 2).text()
        b_rev = self.contacts.item(row, 3).text()
        self.viewer.highlight_pair(f"{a}_{a_rev}", f"{b}_{b_rev}")
