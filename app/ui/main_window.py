from PyQt5 import QtWidgets, QtCore
from app.config.settings import load_admin_settings, load_projects_registry
from app.utils.paths import ensure_project_skeleton
from app.data import store
from app.ui.parts_view import PartsView
from app.ui.analyses_view import AnalysesView
from app.ui.admin_view import AdminView
from app.ui.assemblies_view import AssembliesView
from app.services.watcher import ProjectWatcher


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TF Engineering Data Manager - Sprint 1")
        self.resize(1200, 800)
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

        self.parts_view = PartsView(self.current_project)
        self.analyses_view = AnalysesView(self.current_project)
        self.assemblies_view = AssembliesView(self.current_project)
        self.admin_view = AdminView(self)

        self.tabs.addTab(self.parts_view, "Parts & Revisions")
        self.tabs.addTab(self.analyses_view, "Analyses")
        self.tabs.addTab(self.assemblies_view, "Assemblies")
        self.tabs.addTab(self.admin_view, "Admin")

        ensure_project_skeleton(self.current_project)
        store.seed_tables(self.current_project)

        # Auto-refresh timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh_views)
        self.timer.start(max(1000, int(self.settings.refresh_seconds) * 1000))

        # File watcher
        self.watcher = ProjectWatcher(self.current_project, on_change=self.refresh_views)
        self.watcher.start()

    @property
    def current_project(self) -> str:
        return self.project_combo.currentText() or self.settings.default_project

    def refresh_views(self):
        self.parts_view.refresh()
        self.analyses_view.refresh()
        self.assemblies_view.refresh()

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
