import os
import re
import time
from typing import Dict, List, Tuple
from app.data import store
from app.utils.paths import revision_ppt_path

REV_REGEX = re.compile(r"^(?P<base>.+)_(?P<rev>\d{3})$")


def parse_rev_from_filename(filename: str) -> Tuple[str, int] | None:
    name, _ = os.path.splitext(os.path.basename(filename))
    m = REV_REGEX.match(name)
    if not m:
        return None
    return m.group("base"), int(m.group("rev"))


def ensure_revision_row(project: str, part_base: str, rev_index: int, step_path: str, uploaded_by: str) -> None:
    rows = store.read_all(project, "revisions.csv")
    rev_name = f"{part_base}_{rev_index:03d}"
    exists = any(r.get("project") == project and r.get("part_base") == part_base and r.get("rev_index") == str(rev_index) for r in rows)
    if exists:
        return
    store.append_row(project, "revisions.csv", {
        "project": project,
        "part_base": part_base,
        "rev_index": rev_index,
        "rev_name": rev_name,
        "step_path": step_path,
        "cad_system": "",
        "uploaded_by": uploaded_by,
        "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sha1": "",
        "size_bytes": str(os.path.getsize(step_path)) if os.path.exists(step_path) else "",
        "pending_activation": "true",
        "activated_by": "",
        "activated_at": "",
    })


def has_required_artifacts(project: str, part_base: str, rev_index: int) -> bool:
    ppt = revision_ppt_path(project, part_base, rev_index)
    notes = store.read_all(project, "revision_history.csv")
    has_note = any(
        n.get("project") == project and n.get("part_base") == part_base and n.get("rev_index") == str(rev_index)
        and n.get("what_changed") and n.get("why") and n.get("impacts")
        for n in notes
    )
    return os.path.exists(ppt) and has_note


def activate_revision(project: str, part_base: str, rev_index: int, by_username: str) -> bool:
    if not has_required_artifacts(project, part_base, rev_index):
        return False
    parts = store.read_all(project, "parts.csv")
    for p in parts:
        if p.get("project") == project and p.get("part_base") == part_base:
            p["active_rev"] = str(rev_index)
            p["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    store.write_rows(project, "parts.csv", parts)

    revs = store.read_all(project, "revisions.csv")
    for r in revs:
        if r.get("project") == project and r.get("part_base") == part_base and r.get("rev_index") == str(rev_index):
            r["pending_activation"] = "false"
            r["activated_by"] = by_username
            r["activated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    store.write_rows(project, "revisions.csv", revs)
    return True


def append_revision_note(project: str, part_base: str, rev_index: int, author: str, what_changed: str, why: str, impacts: str, ppt_path: str) -> None:
    store.append_row(project, "revision_history.csv", {
        "project": project,
        "part_base": part_base,
        "rev_index": rev_index,
        "author": author,
        "what_changed": what_changed,
        "why": why,
        "impacts": impacts,
        "ppt_path": ppt_path,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
