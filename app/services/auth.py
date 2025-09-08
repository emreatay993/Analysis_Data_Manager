import getpass
from typing import Optional, Dict
from app.data import store


class CurrentUser:
    def __init__(self, username: str, display_name: str, email: str, role: str, team: str, manager_username: str, active: bool):
        self.username = username
        self.display_name = display_name
        self.email = email
        self.role = role
        self.team = team
        self.manager_username = manager_username
        self.active = active


def get_current_user(project_code: str) -> Optional[CurrentUser]:
    username = getpass.getuser()
    users = store.read_all(project_code, "users.csv")
    for u in users:
        if u.get("username", "").lower() == username.lower():
            return CurrentUser(
                username=u.get("username", username),
                display_name=u.get("display_name", username),
                email=u.get("email", ""),
                role=u.get("role", "designer"),
                team=u.get("team", ""),
                manager_username=u.get("manager_username", ""),
                active=(u.get("active", "true").lower() == "true"),
            )
    # if not found, return minimal user
    return CurrentUser(username=username, display_name=username, email="", role="designer", team="", manager_username="", active=True)


def is_admin(username: str, admin_username: str) -> bool:
    return username.lower() == admin_username.lower()
