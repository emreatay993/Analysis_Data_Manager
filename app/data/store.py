import csv
import os
from typing import List, Dict, Any, Iterable
import portalocker
from app.utils.paths import project_database_dir

CSV_HEADERS = {
    "users.csv": ["username","display_name","email","role","team","manager_username","active"],
    "parts.csv": ["project","part_base","title","owner_username","manager_override_username","active_rev","notes","created_at","updated_at"],
    "revisions.csv": ["project","part_base","rev_index","rev_name","step_path","cad_system","uploaded_by","uploaded_at","sha1","size_bytes","pending_activation","activated_by","activated_at"],
    "revision_history.csv": ["project","part_base","rev_index","author","what_changed","why","impacts","ppt_path","timestamp"],
    "analyses.csv": ["project","analysis_id","part_base","rev_index","requester","analyst","tags","presentation_number","priority","due_date","status","folder_path","created_at","updated_at"],
    "analysis_event_notes.csv": ["project","analysis_id","event_type","author","notes","timestamp"],
    "status_history.csv": ["entity","entity_id","from_status","to_status","by","timestamp","comment"],
}


def _csv_path(project_code: str, name: str) -> str:
    return os.path.join(project_database_dir(project_code), name)


def seed_tables(project_code: str) -> None:
    os.makedirs(project_database_dir(project_code), exist_ok=True)
    for name, headers in CSV_HEADERS.items():
        path = _csv_path(project_code, name)
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)


def read_all(project_code: str, name: str) -> List[Dict[str, Any]]:
    path = _csv_path(project_code, name)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def append_row(project_code: str, name: str, row: Dict[str, Any]) -> None:
    path = _csv_path(project_code, name)
    headers = CSV_HEADERS[name]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with portalocker.Lock(path, "a", timeout=10) as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in headers})


def write_rows(project_code: str, name: str, rows: Iterable[Dict[str, Any]]) -> None:
    path = _csv_path(project_code, name)
    headers = CSV_HEADERS[name]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with portalocker.Lock(tmp, "w", timeout=10) as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in headers})
    os.replace(tmp, path)
