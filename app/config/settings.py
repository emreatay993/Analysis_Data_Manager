import json
import os
from dataclasses import dataclass
from typing import Dict, List

CONFIG_DIR = os.path.join("C:\\TFApp")
ADMIN_CONFIG_PATH = os.path.join(CONFIG_DIR, "admin_config.json")
PROJECTS_REGISTRY_PATH = os.path.join(CONFIG_DIR, "projects.csv")


@dataclass
class Project:
    code: str
    root: str
    active: bool


@dataclass
class AppSettings:
    admin_username: str
    admin_password: str
    default_project: str
    refresh_seconds: int = 3


def ensure_config_dir() -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_admin_settings() -> AppSettings:
    ensure_config_dir()
    if not os.path.exists(ADMIN_CONFIG_PATH):
        default = {
            "admin_username": "admin",
            "admin_password": "admin",
            "default_project": "TF10",
            "ui": {"refresh_seconds": 3},
        }
        with open(ADMIN_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
    with open(ADMIN_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return AppSettings(
        admin_username=data.get("admin_username", "admin"),
        admin_password=data.get("admin_password", "admin"),
        default_project=data.get("default_project", "TF10"),
        refresh_seconds=int(data.get("ui", {}).get("refresh_seconds", 3)),
    )


def load_projects_registry() -> Dict[str, Project]:
    ensure_config_dir()
    projects: Dict[str, Project] = {}
    if not os.path.exists(PROJECTS_REGISTRY_PATH):
        # Create a starter registry
        with open(PROJECTS_REGISTRY_PATH, "w", encoding="utf-8") as f:
            f.write("TF10,C:\\TF10_DemoRoot\\,true\n")
            f.write("TF35,C:\\TF35_DemoRoot\\,true\n")
    with open(PROJECTS_REGISTRY_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                code, root, active_str = parts[:3]
                projects[code] = Project(code=code, root=root, active=active_str.lower() == "true")
    return projects


def get_project_root(code: str) -> str:
    registry = load_projects_registry()
    if code not in registry:
        raise KeyError(f"Project code not found: {code}")
    root = registry[code].root
    return root
