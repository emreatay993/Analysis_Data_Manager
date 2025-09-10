import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.config.settings import get_project_root
from app.services.revision_logic import parse_rev_from_filename, ensure_revision_row
from app.utils.paths import revision_ppt_path
from app.data import store
from time import strftime
import getpass


class CadEventHandler(FileSystemEventHandler):
    def __init__(self, project: str, on_change):
        super().__init__()
        self.project = project
        self.on_change = on_change

    def on_created(self, event):
        self._handle(event)

    def on_modified(self, event):
        self._handle(event)

    def _handle(self, event):
        if event.is_directory:
            return
        path = event.src_path
        lower = path.lower()
        if lower.endswith('.step') or lower.endswith('.stp'):
            parsed = parse_rev_from_filename(path)
            if parsed:
                part_base, rev_index = parsed
                ensure_revision_row(self.project, part_base, rev_index, path, getpass.getuser())
                self.on_change()
        elif lower.endswith('.pptx'):
            # if PPT placed at standard path for some rev, just trigger UI refresh
            self.on_change()


class ProjectWatcher:
    def __init__(self, project: str, on_change):
        self.project = project
        self.on_change = on_change
        self.observer: Observer | None = None

    def start(self):
        self.stop()
        root = get_project_root(self.project)
        cad_dir = os.path.join(root, 'CAD')
        if not os.path.exists(cad_dir):
            return
        handler = CadEventHandler(self.project, self.on_change)
        self.observer = Observer()
        self.observer.schedule(handler, cad_dir, recursive=True)
        self.observer.start()

    def stop(self):
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=2)
            except Exception:
                pass
            self.observer = None
