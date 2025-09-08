from PyQt5 import QtWidgets
from app.config.settings import load_admin_settings, load_projects_registry, ADMIN_CONFIG_PATH, PROJECTS_REGISTRY_PATH
from app.utils.paths import ensure_project_skeleton
from app.data import store
import os
import json


class AdminView(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        cred_box = QtWidgets.QGroupBox("Admin Credentials")
        cred_layout = QtWidgets.QHBoxLayout(cred_box)
        self.user_edit = QtWidgets.QLineEdit()
        self.pass_edit = QtWidgets.QLineEdit(); self.pass_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        btn_save = QtWidgets.QPushButton("Save")
        cred_layout.addWidget(QtWidgets.QLabel("Username:"))
        cred_layout.addWidget(self.user_edit)
        cred_layout.addWidget(QtWidgets.QLabel("Password:"))
        cred_layout.addWidget(self.pass_edit)
        cred_layout.addWidget(btn_save)

        proj_box = QtWidgets.QGroupBox("Projects Registry")
        proj_layout = QtWidgets.QHBoxLayout(proj_box)
        self.proj_code = QtWidgets.QLineEdit()
        self.proj_root = QtWidgets.QLineEdit()
        btn_browse = QtWidgets.QPushButton("Browse")
        btn_add = QtWidgets.QPushButton("Add/Update Project")
        proj_layout.addWidget(QtWidgets.QLabel("Code:"))
        proj_layout.addWidget(self.proj_code)
        proj_layout.addWidget(QtWidgets.QLabel("Root:"))
        proj_layout.addWidget(self.proj_root)
        proj_layout.addWidget(btn_browse)
        proj_layout.addWidget(btn_add)

        layout.addWidget(cred_box)
        layout.addWidget(proj_box)

        # Load existing admin config
        s = load_admin_settings()
        self.user_edit.setText(s.admin_username)
        self.pass_edit.setText(s.admin_password)

        btn_save.clicked.connect(self.save_admin)
        btn_browse.clicked.connect(self.browse_root)
        btn_add.clicked.connect(self.add_project)

    def save_admin(self):
        s = load_admin_settings()
        data = {
            "admin_username": self.user_edit.text().strip() or s.admin_username,
            "admin_password": self.pass_edit.text().strip() or s.admin_password,
            "default_project": s.default_project,
            "ui": {"refresh_seconds": s.refresh_seconds},
        }
        os.makedirs(os.path.dirname(ADMIN_CONFIG_PATH), exist_ok=True)
        with open(ADMIN_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        QtWidgets.QMessageBox.information(self, "Saved", "Admin credentials saved.")

    def browse_root(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Project Root")
        if path:
            if not path.endswith("\\"):
                path += "\\"
            self.proj_root.setText(path)

    def add_project(self):
        code = self.proj_code.text().strip()
        root = self.proj_root.text().strip()
        if not code or not root:
            QtWidgets.QMessageBox.warning(self, "Missing", "Enter code and root.")
            return
        lines = []
        if os.path.exists(PROJECTS_REGISTRY_PATH):
            with open(PROJECTS_REGISTRY_PATH, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
        # Update or append
        found = False
        for i, l in enumerate(lines):
            parts = [p.strip() for p in l.split(",")]
            if parts and parts[0] == code:
                lines[i] = f"{code},{root},true"
                found = True
                break
        if not found:
            lines.append(f"{code},{root},true")
        with open(PROJECTS_REGISTRY_PATH, "w", encoding="utf-8") as f:
            for l in lines:
                f.write(l + "\n")
        ensure_project_skeleton(code)
        store.seed_tables(code)
        QtWidgets.QMessageBox.information(self, "Project saved", f"{code} at {root}")
