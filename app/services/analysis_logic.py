import os
import time
from typing import Dict, List
from app.data import store
from app.utils.paths import analysis_folder
from app.services.notifications import send_email
from app.services import notify_policy

ALLOWED_STATUSES = [
    "need approval (designer)",
    "need approval (analyst)",
    "waiting for designers input",
    "waiting for external input",
    "preprocessing",
    "solving",
    "results are ready for evaluation",
    "postprocessing",
    "presented",
    "archived",
    "deprecated",
]


def get_analysis_row(project: str, analysis_id: str) -> Dict[str, str] | None:
    rows = store.read_all(project, "analyses.csv")
    for r in rows:
        if r.get("project") == project and r.get("analysis_id") == analysis_id:
            return r
    return None


def create_analysis(project: str, analysis_id: str, part_base: str, rev_index: int, requester: str, analyst: str, tags: str) -> None:
    folder = analysis_folder(project, part_base, analysis_id)
    os.makedirs(folder, exist_ok=True)
    row = {
        "project": project,
        "analysis_id": analysis_id,
        "part_base": part_base,
        "rev_index": rev_index,
        "requester": requester,
        "analyst": analyst,
        "tags": tags,
        "presentation_number": "",
        "priority": "",
        "due_date": "",
        "status": "need approval (analyst)",
        "folder_path": folder,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    store.append_row(project, "analyses.csv", row)
    notify_policy.notify_analysis_created(project, row)


def add_analysis_note(project: str, analysis_id: str, event_type: str, author: str, notes: str) -> None:
    store.append_row(project, "analysis_event_notes.csv", {
        "project": project,
        "analysis_id": analysis_id,
        "event_type": event_type,
        "author": author,
        "notes": notes,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


def reassign_analysis(project: str, analysis_id: str, new_analyst: str, author: str, notes: str) -> bool:
    rows = store.read_all(project, "analyses.csv")
    for r in rows:
        if r.get("project") == project and r.get("analysis_id") == analysis_id:
            if (r.get("status", "").lower() in ("presented", "archived")):
                return False
            r["analyst"] = new_analyst
            r["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            store.write_rows(project, "analyses.csv", rows)
            add_analysis_note(project, analysis_id, "reassigned", author, notes)
            return True
    return False


def add_load_case(project: str, analysis_id: str, load_case_id: str, name: str, author: str, notes: str) -> bool:
    r = get_analysis_row(project, analysis_id)
    if not r or (r.get("status", "").lower() in ("presented", "archived")):
        return False
    store.append_row(project, "load_cases.csv", {
        "project": project,
        "analysis_id": analysis_id,
        "load_case_id": load_case_id,
        "name": name,
        "notes": notes,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    add_analysis_note(project, analysis_id, "new_load_case", author, notes)
    return True


def change_status(project: str, analysis_id: str, new_status: str, by: str, comment: str, presentation_number: str = "") -> bool:
    if new_status not in ALLOWED_STATUSES:
        return False
    rows = store.read_all(project, "analyses.csv")
    row_obj = None
    old_status = None
    for r in rows:
        if r.get("project") == project and r.get("analysis_id") == analysis_id:
            row_obj = r
            old_status = r.get("status", "")
            # Freeze: once presented, only allow archive
            if (old_status or "").lower() == "presented" and new_status != "archived":
                return False
            if (old_status or "").lower() == "archived":
                return False
            r["status"] = new_status
            if new_status == "presented":
                r["presentation_number"] = presentation_number
            r["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            break
    if old_status is None:
        return False
    store.write_rows(project, "analyses.csv", rows)
    store.append_row(project, "status_history.csv", {
        "entity": "analysis",
        "entity_id": analysis_id,
        "from_status": old_status,
        "to_status": new_status,
        "by": by,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "comment": comment,
    })
    if row_obj is not None:
        notify_policy.notify_status_change(project, row_obj)
    return True
