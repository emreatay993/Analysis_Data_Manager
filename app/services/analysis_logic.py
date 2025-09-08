import os
import time
from typing import Dict
from app.data import store
from app.utils.paths import analysis_folder


def create_analysis(project: str, analysis_id: str, part_base: str, rev_index: int, requester: str, analyst: str, tags: str) -> None:
    folder = analysis_folder(project, part_base, analysis_id)
    os.makedirs(folder, exist_ok=True)
    store.append_row(project, "analyses.csv", {
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
    })


def add_analysis_note(project: str, analysis_id: str, event_type: str, author: str, notes: str) -> None:
    store.append_row(project, "analysis_event_notes.csv", {
        "project": project,
        "analysis_id": analysis_id,
        "event_type": event_type,
        "author": author,
        "notes": notes,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
