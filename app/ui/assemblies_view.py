from PyQt5 import QtWidgets
from app.data import store
from app.assembly.contact_detection import compute_contacts


class AssembliesView(QtWidgets.QWidget):
    def __init__(self, project: str):
        super().__init__()
        self._project = project
        self._setup_ui()
        self.refresh()

    def set_project(self, project: str):
        self._project = project
        self.refresh()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        actions = QtWidgets.QHBoxLayout()
        self.btn_new = QtWidgets.QPushButton("New Assembly")
        self.btn_add_member = QtWidgets.QPushButton("Add Member")
        self.btn_contacts = QtWidgets.QPushButton("Compute Contacts")
        actions.addWidget(self.btn_new)
        actions.addWidget(self.btn_add_member)
        actions.addWidget(self.btn_contacts)

        self.assemblies = QtWidgets.QComboBox()
        self.members = QtWidgets.QTableWidget()
        self.members.setColumnCount(3)
        self.members.setHorizontalHeaderLabels(["Part", "Rev", "Included"])
        self.members.horizontalHeader().setStretchLastSection(True)

        self.contacts = QtWidgets.QTableWidget()
        self.contacts.setColumnCount(6)
        self.contacts.setHorizontalHeaderLabels(["A Part","A Rev","B Part","B Rev","Relation","Min Gap (mm)"])
        self.contacts.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(actions)
        layout.addWidget(QtWidgets.QLabel("Assembly:"))
        layout.addWidget(self.assemblies)
        layout.addWidget(QtWidgets.QLabel("Members:"))
        layout.addWidget(self.members)
        layout.addWidget(QtWidgets.QLabel("Contacts:"))
        layout.addWidget(self.contacts)

        self.btn_new.clicked.connect(self.on_new)
        self.btn_add_member.clicked.connect(self.on_add_member)
        self.btn_contacts.clicked.connect(self.on_contacts)
        self.assemblies.currentTextChanged.connect(self.refresh_members)

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
        if not aid:
            self.members.setRowCount(0)
            self.contacts.setRowCount(0)
            return
        m = [r for r in store.read_all(self._project, "assembly_members.csv") if r.get("project") == self._project and r.get("assembly_id") == aid]
        self.members.setRowCount(len(m))
        for i, r in enumerate(m):
            vals = [r.get("part_base",""), r.get("rev_index",""), r.get("included","true")]
            for c, v in enumerate(vals):
                self.members.setItem(i, c, QtWidgets.QTableWidgetItem(v))
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

    def on_contacts(self):
        aid = self.assemblies.currentText()
        if not aid:
            return
        m = [r for r in store.read_all(self._project, "assembly_members.csv") if r.get("project") == self._project and r.get("assembly_id") == aid and (r.get("included","true") or "").lower()=="true"]
        members = [(r.get("part_base",""), int(r.get("rev_index","0") or 0)) for r in m]
        contacts = compute_contacts(self._project, aid, members)
        # Overwrite contacts for this assembly
        allc = [c for c in store.read_all(self._project, "contacts.csv") if not (c.get("project") == self._project and c.get("assembly_id") == aid)]
        allc.extend(contacts)
        store.write_rows(self._project, "contacts.csv", allc)
        self.refresh_members()
