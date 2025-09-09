from PyQt5 import QtWidgets
from app.data import store
from app.services.analysis_logic import create_analysis, add_analysis_note, reassign_analysis, add_load_case, change_status, ALLOWED_STATUSES
from app.services.auth import get_current_user
from app.services.notifications import send_email
from app.services.exporter import export_project_summary
from app.utils.paths import get_project_root


class AnalysesView(QtWidgets.QWidget):
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
        self.btn_create = QtWidgets.QPushButton("Create Analysis (notes required)")
        self.btn_reassign = QtWidgets.QPushButton("Reassign (notes required)")
        self.btn_status = QtWidgets.QPushButton("Change Status")
        self.btn_loadcase = QtWidgets.QPushButton("Add Load Case (notes required)")
        self.btn_export = QtWidgets.QPushButton("Export to Excel")
        actions_layout.addWidget(self.btn_create)
        actions_layout.addWidget(self.btn_reassign)
        actions_layout.addWidget(self.btn_status)
        actions_layout.addWidget(self.btn_loadcase)
        actions_layout.addWidget(self.btn_export)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Analysis ID","Part","Rev","Requester","Analyst","Status","Tags","Presentation #"])
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(actions_layout)
        layout.addWidget(self.table)

        self.btn_create.clicked.connect(self.on_create)
        self.btn_reassign.clicked.connect(self.on_reassign)
        self.btn_status.clicked.connect(self.on_status)
        self.btn_loadcase.clicked.connect(self.on_load_case)
        self.btn_export.clicked.connect(self.on_export)

    def refresh(self):
        store.seed_tables(self._project)
        rows = [r for r in store.read_all(self._project, "analyses.csv") if r.get("project") == self._project]
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [
                r.get("analysis_id", ""),
                r.get("part_base", ""),
                r.get("rev_index", ""),
                r.get("requester", ""),
                r.get("analyst", ""),
                r.get("status", ""),
                r.get("tags", ""),
                r.get("presentation_number", ""),
            ]
            for c, v in enumerate(vals):
                self.table.setItem(i, c, QtWidgets.QTableWidgetItem(v))

    def _selected_analysis_id(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).text()

    def on_create(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Create Analysis")
        form = QtWidgets.QFormLayout(dlg)
        part = QtWidgets.QLineEdit()
        rev = QtWidgets.QSpinBox(); rev.setRange(1, 999)
        analysis_id = QtWidgets.QLineEdit()
        tags = QtWidgets.QLineEdit()
        notes = QtWidgets.QPlainTextEdit()
        form.addRow("Part base:", part)
        form.addRow("Revision index:", rev)
        form.addRow("Analysis ID:", analysis_id)
        form.addRow("Tags (| separated):", tags)
        form.addRow("Notes (required):", notes)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        if not notes.toPlainText().strip():
            QtWidgets.QMessageBox.warning(self, "Notes required", "Please enter notes.")
            return
        user = get_current_user(self._project)
        create_analysis(self._project, analysis_id.text().strip(), part.text().strip(), int(rev.value()), user.username, user.username, tags.text().strip())
        add_analysis_note(self._project, analysis_id.text().strip(), "created", user.username, notes.toPlainText().strip())
        self.refresh()

    def on_reassign(self):
        analysis_id = self._selected_analysis_id()
        if not analysis_id:
            QtWidgets.QMessageBox.information(self, "Select", "Select an analysis row first.")
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Reassign Analysis")
        form = QtWidgets.QFormLayout(dlg)
        new_analyst = QtWidgets.QLineEdit()
        notes = QtWidgets.QPlainTextEdit()
        form.addRow("New analyst username:", new_analyst)
        form.addRow("Notes (required):", notes)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        if not new_analyst.text().strip() or not notes.toPlainText().strip():
            QtWidgets.QMessageBox.warning(self, "Missing", "Provide new analyst and notes.")
            return
        user = get_current_user(self._project)
        reassign_analysis(self._project, analysis_id, new_analyst.text().strip(), user.username, notes.toPlainText().strip())
        self.refresh()

    def on_load_case(self):
        analysis_id = self._selected_analysis_id()
        if not analysis_id:
            QtWidgets.QMessageBox.information(self, "Select", "Select an analysis row first.")
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Add Load Case")
        form = QtWidgets.QFormLayout(dlg)
        lc_id = QtWidgets.QLineEdit()
        name = QtWidgets.QLineEdit()
        notes = QtWidgets.QPlainTextEdit()
        form.addRow("Load case ID:", lc_id)
        form.addRow("Name:", name)
        form.addRow("Notes (required):", notes)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        if not lc_id.text().strip() or not notes.toPlainText().strip():
            QtWidgets.QMessageBox.warning(self, "Missing", "Provide load case ID and notes.")
            return
        user = get_current_user(self._project)
        add_load_case(self._project, analysis_id, lc_id.text().strip(), name.text().strip(), user.username, notes.toPlainText().strip())
        self.refresh()

    def on_status(self):
        analysis_id = self._selected_analysis_id()
        if not analysis_id:
            QtWidgets.QMessageBox.information(self, "Select", "Select an analysis row first.")
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Change Status")
        form = QtWidgets.QFormLayout(dlg)
        status_combo = QtWidgets.QComboBox(); status_combo.addItems(ALLOWED_STATUSES)
        comment = QtWidgets.QPlainTextEdit()
        pres = QtWidgets.QLineEdit()
        form.addRow("New status:", status_combo)
        form.addRow("Comment:", comment)
        form.addRow("Presentation # (if presented):", pres)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        new_status = status_combo.currentText()
        if new_status == "presented" and not pres.text().strip():
            QtWidgets.QMessageBox.warning(self, "Required", "Presentation number is required for 'presented'.")
            return
        user = get_current_user(self._project)
        ok = change_status(self._project, analysis_id, new_status, user.username, comment.toPlainText().strip(), presentation_number=pres.text().strip())
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Failed", "Status change failed.")
            return
        self.refresh()

    def on_export(self):
        out_dir = get_project_root(self._project) + "Reports\\"
        path = export_project_summary(self._project, out_dir)
        QtWidgets.QMessageBox.information(self, "Exported", f"Saved to {path}")
