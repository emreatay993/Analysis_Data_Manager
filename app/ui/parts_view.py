from PyQt5 import QtWidgets
from app.data import store
from app.services import revision_logic
from app.services.auth import get_current_user
from app.utils.paths import revision_ppt_path
import os


class PartsView(QtWidgets.QWidget):
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

        actions_layout = QtWidgets.QHBoxLayout()
        self.btn_ingest = QtWidgets.QPushButton("Ingest STEP as New Revision")
        self.btn_activate = QtWidgets.QPushButton("Activate Selected Revision (Owner Only)")
        self.btn_add_notes = QtWidgets.QPushButton("Add Notes & PPT Path")
        actions_layout.addWidget(self.btn_ingest)
        actions_layout.addWidget(self.btn_add_notes)
        actions_layout.addWidget(self.btn_activate)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Part", "Owner", "Active Rev", "Latest Rev", "Pending?", "PPT Exists?"])
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(actions_layout)
        layout.addWidget(self.table)

        self.btn_ingest.clicked.connect(self.on_ingest)
        self.btn_add_notes.clicked.connect(self.on_add_notes)
        self.btn_activate.clicked.connect(self.on_activate)

    def refresh(self):
        store.seed_tables(self._project)
        all_parts = store.read_all(self._project, "parts.csv")
        all_revs = store.read_all(self._project, "revisions.csv")

        # Filter only rows for the active project and with a non-empty part_base
        parts = [p for p in all_parts if p.get("project") == self._project and (p.get("part_base") or "").strip()]
        revs = [r for r in all_revs if r.get("project") == self._project and (r.get("part_base") or "").strip()]

        latest_rev_by_part = {}
        pending_by_part = {}
        for r in revs:
            part = (r.get("part_base") or "").strip()
            try:
                rev = int(r.get("rev_index", "0") or 0)
            except ValueError:
                rev = 0
            if not part:
                continue
            latest_rev_by_part[part] = max(latest_rev_by_part.get(part, 0), rev)
            if (r.get("pending_activation", "false") or "").lower() == "true":
                pending_by_part[part] = True

        # PPT existence: check for latest rev only
        ppt_by_part = {}
        for part, rev in latest_rev_by_part.items():
            if rev > 0:
                ppt_by_part[part] = os.path.exists(revision_ppt_path(self._project, part, rev))
            else:
                ppt_by_part[part] = False

        self.table.setRowCount(len(parts))
        row_idx = 0
        for p in parts:
            part = (p.get("part_base") or "").strip()
            owner = p.get("owner_username", "")
            active_rev = p.get("active_rev", "")
            latest = latest_rev_by_part.get(part, 0)
            latest_str = str(latest) if latest > 0 else ""
            pending = "Yes" if pending_by_part.get(part, False) else "No"
            ppt_exists = "Yes" if ppt_by_part.get(part, False) else "No"

            for col, val in enumerate([part, owner, active_rev, latest_str, pending, ppt_exists]):
                self.table.setItem(row_idx, col, QtWidgets.QTableWidgetItem(val))
            row_idx += 1

    def on_ingest(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select STEP file", filter="STEP Files (*.step *.stp)")
        if not path:
            return
        parsed = revision_logic.parse_rev_from_filename(path)
        if not parsed:
            QtWidgets.QMessageBox.warning(self, "Invalid filename", "Filename must end with _NNN, e.g., PART_012.step")
            return
        part_base, rev_index = parsed
        user = get_current_user(self._project)
        revision_logic.ensure_revision_row(self._project, part_base, rev_index, path, user.username)
        # Ensure part exists
        parts = store.read_all(self._project, "parts.csv")
        if not any(p.get("part_base") == part_base for p in parts):
            from time import strftime
            store.append_row(self._project, "parts.csv", {
                "project": self._project,
                "part_base": part_base,
                "title": part_base,
                "owner_username": user.username,
                "manager_override_username": "",
                "active_rev": "",
                "notes": "",
                "created_at": strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": strftime("%Y-%m-%d %H:%M:%S"),
            })
        self.refresh()

    def on_add_notes(self):
        row = self.table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.information(self, "Select", "Select a part row first.")
            return
        part = self.table.item(row, 0).text()
        rev_text, ok = QtWidgets.QInputDialog.getInt(self, "Revision Index", "Enter revision index (NNN):", 1, 1, 999, 1)
        if not ok:
            return
        what, ok1 = QtWidgets.QInputDialog.getMultiLineText(self, "What changed", "Describe what changed:")
        if not ok1:
            return
        why, ok2 = QtWidgets.QInputDialog.getMultiLineText(self, "Why", "Why changed:")
        if not ok2:
            return
        impacts, ok3 = QtWidgets.QInputDialog.getMultiLineText(self, "Impacts", "Impacts:")
        if not ok3:
            return
        ppt_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select PPT", filter="PowerPoint (*.pptx)")
        if not ppt_path:
            return
        user = get_current_user(self._project)
        revision_logic.append_revision_note(self._project, part, rev_text, user.username, what, why, impacts, ppt_path)
        self.refresh()

    def on_activate(self):
        row = self.table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.information(self, "Select", "Select a part row first.")
            return
        part = self.table.item(row, 0).text()
        parts = store.read_all(self._project, "parts.csv")
        owner = None
        for p in parts:
            if p.get("part_base") == part:
                owner = p.get("owner_username")
                break
        user = get_current_user(self._project)
        if owner and owner.lower() != user.username.lower():
            QtWidgets.QMessageBox.warning(self, "Permission", "Only the part owner can activate a revision.")
            return
        rev_index, ok = QtWidgets.QInputDialog.getInt(self, "Activate Revision", "Enter revision index (NNN):", 1, 1, 999, 1)
        if not ok:
            return
        if not revision_logic.has_required_artifacts(self._project, part, rev_index):
            QtWidgets.QMessageBox.warning(self, "Missing artifacts", "Notes and PPT are required before activation.")
            return
        ok2 = revision_logic.activate_revision(self._project, part, rev_index, user.username)
        if not ok2:
            QtWidgets.QMessageBox.warning(self, "Activation failed", "Could not activate revision.")
            return
        QtWidgets.QMessageBox.information(self, "Activated", f"{part} rev {rev_index:03d} activated.")
        self.refresh()
