from typing import List, Tuple
from app.data import store
from app.services.notifications import send_email


def _get_user_email(project: str, username: str) -> str:
    users = store.read_all(project, "users.csv")
    for u in users:
        if u.get("username", "").lower() == (username or "").lower():
            return u.get("email", "")
    return ""


def notify_analysis_created(project: str, analysis_row: dict) -> None:
    part_owner = _find_part_owner(project, analysis_row.get("part_base", ""))
    to = []
    cc = []
    to.append(_get_user_email(project, analysis_row.get("analyst", "")))
    to.append(_get_user_email(project, analysis_row.get("requester", "")))
    if part_owner:
        to.append(_get_user_email(project, part_owner))
    send_email(
        subject=f"[{project}] Analysis {analysis_row.get('analysis_id','')} created",
        body=f"Analysis {analysis_row.get('analysis_id','')} created for part {analysis_row.get('part_base','')} rev {analysis_row.get('rev_index','')}",
        to=[e for e in to if e],
        cc=cc,
    )


def _find_part_owner(project: str, part_base: str) -> str:
    parts = store.read_all(project, "parts.csv")
    for p in parts:
        if p.get("project") == project and p.get("part_base") == part_base:
            return p.get("owner_username", "")
    return ""


def notify_status_change(project: str, analysis_row: dict) -> None:
    status = analysis_row.get("status", "")
    to = []
    cc = []
    owner = _find_part_owner(project, analysis_row.get("part_base", ""))
    to.append(_get_user_email(project, analysis_row.get("requester", "")))
    if owner:
        to.append(_get_user_email(project, owner))
    # CC manager on results ready and presented
    if status in ("results are ready for evaluation", "presented") and owner:
        users = store.read_all(project, "users.csv")
        mgr_user = None
        for u in users:
            if u.get("username", "") == owner:
                mgr_user = u.get("manager_username", "")
                break
        if mgr_user:
            cc.append(_get_user_email(project, mgr_user))
    send_email(
        subject=f"[{project}] Analysis {analysis_row.get('analysis_id','')} status: {status}",
        body=f"Status changed to {status} for analysis {analysis_row.get('analysis_id','')} ({analysis_row.get('part_base','')} rev {analysis_row.get('rev_index','')})",
        to=[e for e in to if e],
        cc=[e for e in cc if e],
    )

