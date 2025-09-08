import os
from app.config.settings import get_project_root


def project_database_dir(project_code: str) -> str:
    return os.path.join(get_project_root(project_code), "Database")


def ensure_project_skeleton(project_code: str) -> None:
    root = get_project_root(project_code)
    for sub in [
        "Database",
        os.path.join("CAD", "Parts"),
        "Analysis",
        "Reports",
        "Locks",
        "Temp",
    ]:
        os.makedirs(os.path.join(root, sub), exist_ok=True)


def cad_part_rev_dir(project_code: str, part_base: str, rev_index: int) -> str:
    root = get_project_root(project_code)
    return os.path.join(root, "CAD", "Parts", part_base, f"rev_{rev_index:03d}")


def revision_ppt_path(project_code: str, part_base: str, rev_index: int) -> str:
    return os.path.join(cad_part_rev_dir(project_code, part_base, rev_index), "Change_Presentation.pptx")


def analysis_folder(project_code: str, part_base: str, analysis_id: str) -> str:
    root = get_project_root(project_code)
    return os.path.join(root, "Analysis", part_base, analysis_id)
