from PyQt5 import QtWidgets
from app.data import store
from app.services.analysis_logic import create_analysis, add_analysis_note
from app.services.auth import get_current_user


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
        actions_layout.addWidget(self.btn_create)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Analysis ID","Part","Rev","Requester","Analyst","Status","Tags"])
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(actions_layout)
        layout.addWidget(self.table)

        self.btn_create.clicked.connect(self.on_create)

    def refresh(self):
        store.seed_tables(self._project)
        rows = store.read_all(self._project, "analyses.csv")
        rows = [r for r in rows if r.get("project") == self._project]
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
            ]
            for c, v in enumerate(vals):
                self.table.setItem(i, c, QtWidgets.QTableWidgetItem(v))

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
