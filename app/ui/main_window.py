from PyQt5 import QtWidgets, QtCore
from app.config.settings import load_admin_settings, load_projects_registry
from app.utils.paths import ensure_project_skeleton
from app.data import store
from app.ui.parts_view import PartsView
from app.ui.analyses_view import AnalysesView
from app.ui.admin_view import AdminView
from app.ui.assemblies_view import AssembliesView
from app.services.watcher import ProjectWatcher
from app.ui.styles import app_stylesheet


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TF Engineering Data Manager - Sprint 1")
        # Set a slightly larger normal/restored size
        self.resize(1440, 900)
        self.settings = load_admin_settings()
        self.projects = load_projects_registry()

        self.project_combo = QtWidgets.QComboBox()
        for code, p in self.projects.items():
            if p.active:
                self.project_combo.addItem(code)
        default_index = max(0, self.project_combo.findText(self.settings.default_project))
        self.project_combo.setCurrentIndex(default_index)
        self.project_combo.currentTextChanged.connect(self.on_project_changed)

        toolbar = self.addToolBar("Project")
        toolbar.addWidget(QtWidgets.QLabel(" Project: "))
        toolbar.addWidget(self.project_combo)

        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)
        # Apply global app stylesheet for buttons and tabs
        try:
            self.setStyleSheet(app_stylesheet)
        except Exception:
            pass

        self.parts_view = PartsView(self.current_project)
        self.analyses_view = AnalysesView(self.current_project)
        self.assemblies_view = AssembliesView(self.current_project, self)
        self._admin_view = None  # lazy create
        self._admin_placeholder = QtWidgets.QWidget()
        _ph_layout = QtWidgets.QVBoxLayout(self._admin_placeholder)
        _ph_layout.addStretch(1)
        _ph_label = QtWidgets.QLabel("Admin panel is locked. Select the tab to unlock.")
        _ph_label.setAlignment(QtCore.Qt.AlignCenter)
        _ph_layout.addWidget(_ph_label)
        _ph_layout.addStretch(1)

        self.tabs.addTab(self.parts_view, "Parts & Revisions")
        self.tabs.addTab(self.assemblies_view, "Assemblies")
        self.tabs.addTab(self.analyses_view, "Analyses")
        self._admin_tab_index = self.tabs.addTab(self._admin_placeholder, "Admin")
        # Wire parts selection to 3D viewer preview when no assembly is showing
        try:
            self.parts_view.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            self.parts_view.table.itemSelectionChanged.connect(self._on_parts_selection_changed)
        except Exception:
            pass

        # Admin lock state and tab guard
        self._admin_unlocked = False
        self._last_tab_index = 0
        try:
            self.tabs.currentChanged.connect(self._on_tab_changed)
        except Exception:
            pass

        ensure_project_skeleton(self.current_project)
        store.seed_tables(self.current_project)

        # Auto-refresh timer (avoid refreshing Assemblies to keep camera stable)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh_views)
        self.timer.start(max(1000, int(self.settings.refresh_seconds) * 1000))

        # File watcher
        self.watcher = ProjectWatcher(self.current_project, on_change=self.refresh_views)
        self.watcher.start()
        # Restore main window geometry (do not restore dock layout)
        self._restore_window_state()
        # Ensure maximized at first show if nothing to restore
        try:
            QtCore.QTimer.singleShot(0, self._restore_window_state)
        except Exception:
            pass

    @property
    def current_project(self) -> str:
        return self.project_combo.currentText() or self.settings.default_project

    def refresh_views(self):
        # Refresh parts and analyses frequently; leave assemblies view untouched to avoid recentering
        self.parts_view.refresh()
        self.analyses_view.refresh()

    def on_project_changed(self, code: str):
        ensure_project_skeleton(code)
        store.seed_tables(code)
        self.parts_view.set_project(code)
        self.analyses_view.set_project(code)
        self.assemblies_view.set_project(code)
        # Restart watcher for new project
        try:
            self.watcher.stop()
        except Exception:
            pass
        self.watcher = ProjectWatcher(self.current_project, on_change=self.refresh_views)
        self.watcher.start()
        self.statusBar().showMessage(f"Project switched to {code}")

    def _settings(self) -> QtCore.QSettings:
        return QtCore.QSettings("TFEngineering", "AnalysisDataManager")

    def _restore_window_state(self) -> None:
        try:
            s = self._settings()
            try:
                geom = s.value("mainWindow/geometry", None, type=QtCore.QByteArray)
            except Exception:
                geom = s.value("mainWindow/geometry", None)
            restored_any = False
            if isinstance(geom, (bytes, bytearray, QtCore.QByteArray)) and len(geom) > 0:
                try:
                    self.restoreGeometry(geom)
                    restored_any = True
                except Exception:
                    pass
            if not restored_any:
                # First run: start maximized by default
                try:
                    self.setWindowState(self.windowState() | QtCore.Qt.WindowMaximized)
                except Exception:
                    pass
        except Exception:
            try:
                self.setWindowState(self.windowState() | QtCore.Qt.WindowMaximized)
            except Exception:
                pass

    def closeEvent(self, event):
        # Persist main window geometry and dock layout for next session
        try:
            s = self._settings()
            s.setValue("mainWindow/geometry", self.saveGeometry())
        except Exception:
            pass
        super().closeEvent(event)

    def _on_tab_changed(self, index: int) -> None:
        try:
            if index == getattr(self, '_admin_tab_index', -1) and not getattr(self, '_admin_unlocked', False):
                if not self._require_admin_password():
                    # Revert to previous tab if authentication failed/cancelled
                    try:
                        block_prev = self.tabs.blockSignals(True)
                        self.tabs.setCurrentIndex(self._last_tab_index)
                        self.tabs.blockSignals(block_prev)
                    except Exception:
                        pass
                    return
                # Unlock and swap placeholder with real admin view
                try:
                    if self._admin_view is None:
                        self._admin_view = AdminView(self)
                    block_prev = self.tabs.blockSignals(True)
                    self.tabs.removeTab(self._admin_tab_index)
                    self._admin_tab_index = self.tabs.insertTab(index, self._admin_view, "Admin")
                    self.tabs.setCurrentIndex(self._admin_tab_index)
                    self.tabs.blockSignals(block_prev)
                except Exception:
                    pass
                self._admin_unlocked = True
            # Track last non-admin index to revert to on failed attempts
            if index != getattr(self, '_admin_tab_index', -1):
                self._last_tab_index = index
        except Exception:
            pass

    def _require_admin_password(self) -> bool:
        # Prompt for admin password; return True if correct
        try:
            s = load_admin_settings()
            pwd, ok = QtWidgets.QInputDialog.getText(
                self,
                "Admin Login",
                "Enter admin password:",
                QtWidgets.QLineEdit.Password,
                ""
            )
            if not ok:
                return False
            if (pwd or "") == (s.admin_password or ""):
                return True
            QtWidgets.QMessageBox.warning(self, "Access denied", "Incorrect admin password.")
            return False
        except Exception:
            return False
    def _on_parts_selection_changed(self) -> None:
        try:
            sel = self.parts_view.table.selectionModel()
            if sel is None or not sel.hasSelection():
                # Clear any assembly highlights when selection is cleared
                try:
                    self.assemblies_view.viewer.clear_highlight()
                except Exception:
                    pass
                return
            # Collect selected parts and their latest revs from the table
            rows = sorted({ix.row() for ix in sel.selectedIndexes()})
            parts: list[tuple[str, int]] = []
            for r in rows:
                try:
                    part = (self.parts_view.table.item(r, 0) or QtWidgets.QTableWidgetItem("")).text().strip()
                    # Prefer Active Rev if present; else Latest Rev
                    active_str = (self.parts_view.table.item(r, 2) or QtWidgets.QTableWidgetItem("")).text().strip()
                    latest_str = (self.parts_view.table.item(r, 3) or QtWidgets.QTableWidgetItem("")).text().strip()
                    src = active_str if active_str.isdigit() else latest_str
                    rev = int(src) if src.isdigit() else 0
                    if part:
                        parts.append((part, rev))
                except Exception:
                    continue
            if not parts:
                return
            # Ask assemblies view to preview parts only if no assembly is displayed
            try:
                self.assemblies_view.show_parts_preview(parts)
            except Exception:
                pass
        except Exception:
            pass

    def reload_projects(self, select_code: str | None = None) -> None:
        """Reload the projects registry and repopulate the combobox immediately."""
        current = self.project_combo.currentText()
        self.projects = load_projects_registry()
        block_prev = self.project_combo.blockSignals(True)
        self.project_combo.clear()
        for code, p in self.projects.items():
            if p.active:
                self.project_combo.addItem(code)
        target = select_code or current or self.settings.default_project
        idx = self.project_combo.findText(target)
        if idx >= 0:
            self.project_combo.setCurrentIndex(idx)
        elif self.project_combo.count() > 0:
            self.project_combo.setCurrentIndex(0)
        self.project_combo.blockSignals(block_prev)
        # Ensure views and folders are ready for the currently selected project
        self.on_project_changed(self.current_project)
