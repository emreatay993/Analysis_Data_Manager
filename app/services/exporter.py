import os
import pandas as pd
from app.data import store


def export_project_summary(project: str, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    parts = store.read_all(project, "parts.csv")
    revs = store.read_all(project, "revisions.csv")
    analyses = store.read_all(project, "analyses.csv")
    status_history = store.read_all(project, "status_history.csv")
    path = os.path.join(out_dir, f"{project}_summary.xlsx")
    with pd.ExcelWriter(path, engine="xlsxwriter") as w:
        pd.DataFrame(parts).to_excel(w, sheet_name="parts", index=False)
        pd.DataFrame(revs).to_excel(w, sheet_name="revisions", index=False)
        pd.DataFrame(analyses).to_excel(w, sheet_name="analyses", index=False)
        pd.DataFrame(status_history).to_excel(w, sheet_name="status_history", index=False)
    return path
