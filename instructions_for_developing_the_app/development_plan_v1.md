## TF Engineering Data Manager — Full Development Plan (v1)

Author: You + Assistant  
Scope: PyQt5 desktop app on Windows for multi-project CAD/Analysis data management using CSV files on shared/local roots.  
Status: Drafted from decisions confirmed in chat; defaults applied where not explicitly set.

---

### 1) Vision and Non‑Goals
- **Vision**: A Windows desktop tool that centralizes part/revision tracking, analysis lifecycle, assembly checks, and notifications for design and structural teams, using CSVs on a shared folder.
- **Primary users**: Designers, Analysts, Managers; Admin (you) via an in-app admin password.
- **Non‑goals (v1)**: No external database server; no internet services; no advanced 3D meshing; no automated CAD transforms (parts assumed in engine global coordinates).

---

### 2) Users, Roles, and Permissions
- **Roles**
  - **Designer**: Edit only their parts. Create new part revisions (STEP), add mandatory notes + PPT, request/perform activation for own parts.
  - **Analyst**: Create/reassign analyses, update statuses/tags/notes, add load cases. Cannot activate part revisions.
  - **Manager**: Read-only access; export to Excel.
  - **Admin**: Manage projects, users, assignments, parts registry, and app settings via admin username+password.
- **Authentication**
  - Log in as current Windows user via `getpass.getuser()`; role and permissions sourced from CSV (`users.csv`, `parts.csv`, `assignments` not needed initially since one designer per part).
  - Single local admin credentials stored in config; changeable from Admin panel.
- **Permission rules**
  - Designer can edit rows where `parts.owner_username == current_user`.
  - Analyst can edit their own `analyses.csv` rows.
  - Manager is read-only everywhere.
  - Admin can override any operation.

---

### 3) Multi‑Project Support and Roots
- **Project registry file**: `C:\TFApp\projects.csv` (demo); move to a shared path later without code changes.
- **Configurable roots per project**
  - Example rows:
```
TF10,C:\TF10_DemoRoot\,true
TF35,C:\TF35_DemoRoot\,true
```
- **Admin workflow**
  - Add project → choose root path → app seeds folder skeleton and empty CSVs → define parts and assign owners.

---

### 4) Folder Structure per Project Root
Under each project root (e.g., `C:\TF10_DemoRoot\`):
- `Database\` — all CSVs for this project
- `CAD\Parts\<part_base>\rev_<nn>\` — STEP and revision PPT
- `Analysis\<part_base>\<analysis_id>\` — analysis working folders
- `Reports\` — generated Excel summaries
- `Locks\` — lock files for safe writes
- `Attachments\` — optional area for additional files (future)
- `Temp\` — transient artifacts

Standard revision artifacts per revision:
- STEP: `CAD\Parts\<part_base>\rev_<nn>\*.step` (name must contain `_<nnn>` suffix)
- PPT: `CAD\Parts\<part_base>\rev_<nn>\Change_Presentation.pptx`

---

### 5) Data Storage — CSV Files (Schemas)
All CSVs are per-project in `Database\`.

- `projects.csv` (global, outside projects): `project_code,root_path,active`
- `users.csv`: `username,display_name,email,role,team,manager_username,active`
- `parts.csv`: `project,part_base,title,owner_username,manager_override_username,active_rev,notes,created_at,updated_at`
- `revisions.csv`: `project,part_base,rev_index,rev_name,step_path,cad_system,uploaded_by,uploaded_at,sha1,size_bytes,pending_activation,activated_by,activated_at`
- `revision_history.csv`: `project,part_base,rev_index,author,what_changed,why,impacts,ppt_path,timestamp`
- `analyses.csv`: `project,analysis_id,part_base,rev_index,requester,analyst,tags,presentation_number,priority,due_date,status,folder_path,created_at,updated_at`
- `analysis_event_notes.csv`: `project,analysis_id,event_type,author,notes,timestamp`
- `load_cases.csv`: `project,analysis_id,load_case_id,name,notes,created_at`
- `status_history.csv`: `entity,entity_id,from_status,to_status,by,timestamp,comment`
- `assemblies.csv`: `project,assembly_id,name,created_by,created_at,note`
- `assembly_members.csv`: `project,assembly_id,part_base,rev_index,included`
- `contacts.csv`: `project,assembly_id,a_part,a_rev,b_part,b_rev,relation,min_gap_mm,contact_area_mm2,note`
- `events.csv` (append-only audit): `event_id,timestamp,username,action,entity,entity_id,payload_json`

Constraints (enforced in code):
- `revisions`: unique `(project, part_base, rev_index)`; `rev_name` matches `^.+_(\d{3})$`.
- `analyses`: unique `(project, analysis_id)`.
- `status_history`: append-only.
- `users.role ∈ {designer, analyst, manager, admin}`.

---

### 6) Naming Conventions and Revision Policy
- Revision name pattern: `part_base` + `_` + zero-padded integer with 3 digits (e.g., `BLD_COVER_012`).
- `rev_index` is the integer (e.g., `12`).
- New STEP files detected with a higher suffix create a `revisions.csv` row with `pending_activation = true`.
- Only the part owner can activate a revision. Activation requires:
  - A `revision_history.csv` entry with non-empty `what_changed`, `why`, `impacts`.
  - The PPT file exists at the standard path.
- On activation:
  - `parts.active_rev` updated to new `rev_index`.
  - Prior active revision is automatically marked “deprecated” (logical state, reflected in UI and filters).
  - `revisions.pending_activation = false`, `activated_by`, `activated_at` set.
  - `status_history` receives an entry for the part entity.

---

### 7) Analysis Lifecycle and Statuses
Statuses (canonical strings):
- `need approval (designer)`
- `need approval (analyst)`
- `waiting for designers input`
- `waiting for external input`
- `preprocessing`
- `solving`
- `results are ready for evaluation`
- `postprocessing`
- `presented`
- `archived`
- `deprecated`

Transitions (typical):
- Approvals → preprocessing → solving → results are ready for evaluation → postprocessing → presented → archived
- Branches: waiting states can return to preprocessing.
- Every change writes to `status_history.csv`.

Analyses may be created against any revision (Flexible policy, default):
- An analysis is “pinned to rev N”. If a newer active revision appears, app shows a banner and offers “Rebase to active_rev”. Admin can enforce strict later.

Required notes/triggers:
- On create/reassign: add an `analysis_event_notes.csv` row (`event_type ∈ {created, reassigned}`).
- On “new load case added”: add a note row.
- On “presented”: `presentation_number` required.

Tags:
- Free-form pipe-separated tags in `analyses.tags` (e.g., `static|bolt|HPC`).

---

### 8) Manager CC Mapping
- Default mapping: resolve manager from `users.manager_username` of the part owner.
- Optional override per part with `parts.manager_override_username` (if present, it is used).
- Used in notifications for “results are ready for evaluation” and “presented”.

---

### 9) Notifications (Outlook via `pywin32`)
Triggers and recipients:
- Part CAD revised (pending): notify part owner. Activation blocked until notes+PPT are present.
- Analysis created/reassigned: notify assigned analyst, requester, and part owner.
- Status hits:
  - `results are ready for evaluation` → requester + part owner + CC manager
  - `presented` → requester + part owner + CC manager
  - `new load case added` → requester + part owner
- No throttling/digests/quiet hours in v1.
- Intranet only; future safeguard to restrict external domains.

Templates (placeholders: `{project}`, `{part_base}`, `{rev_name}`, `{analysis_id}`, `{status}`, `{link}`, `{presentation_number}`):
- Stored in `Database\notifications_templates\*.txt` (optional), else defaults embedded in app.

---

### 10) Assembly Viewer and Contact Detection
- STEP load using `pythonocc-core` (OCC) and embedded Qt OpenGL viewer.
- Parts assumed positioned in the engine global coordinate system (no transforms initially).
- Gap classification:
  - Touching if −0.002 mm ≤ gap ≤ +0.002 mm
  - Penetration if gap < −0.002 mm
  - Clearance otherwise (min positive gap)
- Pipeline:
  - Broad phase: AABB/OBB pair filtering.
  - Narrow phase: shape distance / intersection via OCC extrema.
  - Save results to `contacts.csv`.
- UI: list of contacts with filters; selecting highlights the two parts; overlay heatmap optional in a later version.

---

### 11) Exports and Reports
- Excel exports from filtered tables for managers: parts, revisions, analyses, contacts.
- Stored under `Reports\` per project.
- No PowerPoint/HTML dashboards in v1.

---

### 12) Concurrency, Locking, and Audit
- **Writes** protected by file locks:
  - Use `portalocker` and `.lock` files under `Locks\`.
  - Atomic temp writes then replace target CSV.
- **File watcher**: `watchdog` monitors `CAD\Parts\...\rev_*\` for new/modified STEP/PPT and updates `revisions.csv`/`revision_history.csv` entries, marking pending activation when applicable.
- **Audit**: every mutating action appends an event to `events.csv` with payload JSON (before/after diffs if available).

---

### 13) Performance and Scale Targets
- Scale from you:
  - 5–10 parts per project; up to hundreds of revisions per part.
  - 5–10 concurrent users; up to 20 total users.
- Design choices:
  - CSV + locks is sufficient; 2–5 s auto-refresh per view.
  - Lazy loading and on-demand filtering in UI.
  - Optional in-memory cache invalidated by watcher or timestamps.

---

### 14) Security and Admin
- Single admin username/password stored in an app config file (`admin_config.json`) alongside the app; changeable in Admin panel.
- Admin operations:
  - Add/edit projects (and seed folders/CSVs).
  - Add/edit users and roles.
  - Define parts and assign owners.
  - Override activation and unfreeze/unarchive items if needed.

Note: plaintext admin password is acceptable per your instruction; plan to migrate to hashed credentials in a future hardening step.

---

### 15) Freeze / Archive / Deprecate Policies
- **Freeze**
  - Revisions: freeze on activation. Content/metadata become read-only (comments still allowed).
  - Analyses: freeze at `presented`. Inputs and parameters become read-only; comments allowed.
- **Archive**
  - Manual archive action for frozen analyses; hides from active views; still searchable/exportable.
- **Deprecate**
  - When a new revision activates, the prior active revision is auto-deprecated (excluded from default pickers for new analyses unless Admin overrides).
- **Unfreeze/unarchive**: Admin only.

---

### 16) UI / UX Blueprint (PyQt5)
- **Main window (`QMainWindow`)**
  - Left: `QTreeView` project navigator (Projects → Parts / Analyses / Assemblies / Reports / Admin).
  - Center: tabbed views (Parts & Revisions, Analyses, Assemblies, Notifications, Admin).
  - Top: search bar and quick filters; status bar shows current user/project.
- **Parts & Revisions view**
  - Grid of parts with owner, active rev, latest rev, flags.
  - Detail panel with part metadata, revision list, and activation button (owner only).
  - Actions: “Ingest STEP as new revision”, “Add notes/PPT”, “Request activation”, “Activate” (owner only).
- **Analyses view**
  - Table with filters and a Kanban by status.
  - Create/reassign analysis (notes mandatory).
  - Add load case (notes mandatory).
  - Quick status changes with required fields prompts (e.g., presentation number).
- **Assemblies view**
  - Viewer pane + members list + contacts table.
  - Actions: build assembly from selected parts/revisions; run contact detection; save results.
- **Notifications view**
  - Preview templates, send test email, see last sent logs (read-only summary from `events.csv`).
- **Admin view**
  - Projects management
  - Users & roles
  - Parts registry and ownership
  - Settings (admin username/password)

---

### 17) Configuration Files
- `C:\TFApp\projects.csv` — registry of projects (demo; later on a shared path)
- `admin_config.json` — admin credentials and app options (local)
```json
{
  "admin_username": "admin",
  "admin_password": "your_password",
  "default_project": "TF10",
  "ui": { "refresh_seconds": 3 }
}
```

---

### 18) Dependencies (Python 3.10+ recommended)
- UI: `PyQt5`
- Data: `pandas`
- Locking: `portalocker`
- Watcher: `watchdog`
- Email: `pywin32` (`win32com.client`)
- 3D/STEP: `pythonocc-core` (OCC) [or fallback: `trimesh`, `open3d` (reduced fidelity)]
- Packaging: `pyinstaller`
- Optional utils: `pydantic` for validation, `pyyaml` for config alternates

---

### 19) Application Modules (proposed layout)
- `app/main.py` — entrypoint
- `app/ui/` — Qt widgets, dialogs, models
  - `main_window.py`, `parts_view.py`, `analyses_view.py`, `assemblies_view.py`, `admin_view.py`, `notifications_view.py`
- `app/data/` — CSV IO and models
  - `store.py` (generic read/write with locks), `schemas.py`, `validators.py`
- `app/services/`
  - `auth.py` (current user, role resolution), `notifications.py` (Outlook), `watcher.py` (STEP/PPT), `revision_logic.py`, `analysis_logic.py`, `status_flow.py`
- `app/assembly/`
  - `step_loader.py`, `viewer.py`, `contact_detection.py`
- `app/utils/`
  - `paths.py` (project roots, standard paths), `ids.py`, `logging.py`, `timestamps.py`
- `app/config/`
  - `settings.py` (load `admin_config.json`, `projects.csv`)

---

### 20) Key Behaviors (Algorithmic Summaries)
- **Revision ingestion**
  - Detect `.step` with suffix `_nnn` → parse `rev_index` → add to `revisions.csv` with `pending_activation = true` if new or updated.
  - Prompt designer to fill notes (`what_changed`, `why`, `impacts`) and ensure PPT exists at standard path.
- **Activation (owner only)**
  - Validate required notes + PPT → update `parts.active_rev` and `revisions` → send notification.
- **Analysis creation/reassignment**
  - Collect minimal fields + mandatory note → create folder under `Analysis\<part>\ <analysis_id>\` → notify stakeholders.
- **Status changes**
  - Enforce allowed transitions; capture `presentation_number` when status = `presented`; append to `status_history.csv`.
- **Contact detection**
  - For selected revisions, run broad-phase AABB pairing → narrow-phase OCC extrema → classify and store `contacts.csv`.

---

### 21) IDs and Conventions
- `analysis_id`: `AN-{YYYYMMDD}-{seq4}` within project (e.g., `AN-20250315-0042`).
- `assembly_id`: `AS-{YYYYMMDD}-{seq4}`.
- Load cases: per-analysis incremental numbers or free text IDs.
- All timestamps in local time; stored as ISO 8601.

---

### 22) Validation and Error Handling
- Validate CSV rows on load; display errors in Admin diagnostics.
- Defensive checks before writes; if lock acquisition fails, retry with backoff and clear message to user.
- Missing PPT or notes block activation and show actionable prompts.

---

### 23) Packaging and Deployment
- Build with `pyinstaller --onefile` (plus a version with external data folder).
- First run:
  - Create `admin_config.json` if missing and prompt to set credentials.
  - Locate `C:\TFApp\projects.csv`; if missing, offer to create and add first project.
- Logs go to `%APPDATA%\TFApp\logs\app.log`.

---

### 24) Testing and Acceptance
Manual acceptance scenarios (v1):
- Project creation by Admin; parts defined and owners assigned.
- Designer ingests new STEP, adds notes + PPT, activates revision; notifications sent.
- Analyst creates analysis (notes required), adds load case (notes required), advances statuses; notifications at defined points.
- Manager opens app, filters and exports to Excel.
- Assembly viewer loads two parts and reports contacts per tolerance.
- Concurrency: two users edit different entities without corruption (locks verified).
- Audit: events populated for all mutations.

---

### 25) Initial Backlog and Sprints

#### Sprint 1 (Core skeleton and data)
- Load `projects.csv`; project switcher; seed per-project folder skeleton.
- CSV layer with locked writes and schema validation.
- `users.csv`, `parts.csv`, `revisions.csv`, `revision_history.csv` basic CRUD (with permissions).
- Parts/Revisions view; ingest STEP; notes+PPT enforced; owner-only activation.
- Basic notifications via Outlook for revision activation and analysis creation.
- Minimal Admin panel (projects, users, parts, admin credentials).

Deliverables: running EXE, demo with `TF10` and `TF35`.

#### Sprint 2 (Analyses and statuses)
- Analyses view with create/reassign, tags, load cases (notes required).
- Status transitions + `status_history.csv`; required fields for `presented`.
- Notifications for `results are ready for evaluation`, `presented`, `new load case added`.
- Excel export views.

#### Sprint 3 (Assemblies and contacts)
- STEP viewer embedding.
- Contact detection pipeline and `contacts.csv`.
- UI overlays, filtering, and save/load assembly members.

#### Sprint 4 (Polish and robustness)
- Watchdog integration for STEP/PPT appearance.
- Enhanced filtering/search, saved views.
- Additional Admin tools (bulk import/export).
- Hardened error handling and logs.

---

### 26) Example CSV Headers (ready-to-create)

`users.csv`
```
username,display_name,email,role,team,manager_username,active
```

`parts.csv`
```
project,part_base,title,owner_username,manager_override_username,active_rev,notes,created_at,updated_at
```

`revisions.csv`
```
project,part_base,rev_index,rev_name,step_path,cad_system,uploaded_by,uploaded_at,sha1,size_bytes,pending_activation,activated_by,activated_at
```

`revision_history.csv`
```
project,part_base,rev_index,author,what_changed,why,impacts,ppt_path,timestamp
```

`analyses.csv`
```
project,analysis_id,part_base,rev_index,requester,analyst,tags,presentation_number,priority,due_date,status,folder_path,created_at,updated_at
```

`analysis_event_notes.csv`
```
project,analysis_id,event_type,author,notes,timestamp
```

`load_cases.csv`
```
project,analysis_id,load_case_id,name,notes,created_at
```

`status_history.csv`
```
entity,entity_id,from_status,to_status,by,timestamp,comment
```

`assemblies.csv`
```
project,assembly_id,name,created_by,created_at,note
```

`assembly_members.csv`
```
project,assembly_id,part_base,rev_index,included
```

`contacts.csv`
```
project,assembly_id,a_part,a_rev,b_part,b_rev,relation,min_gap_mm,contact_area_mm2,note
```

`events.csv`
```
event_id,timestamp,username,action,entity,entity_id,payload_json
```

---

### 27) Assumptions and Defaults (changeable later)
- Analyses can target non-active revisions (Flexible) with “pinned” banner and “Rebase” action.
- Manager CC mapping uses owner’s `users.manager_username` unless `parts.manager_override_username` is set.
- No throttling/digest/quiet hours for emails in v1.
- Admin password stored in plaintext config per your instruction.

---

### 28) Future Enhancements (Roadmap)
- Hash admin credentials; optional AD integration to resolve display names/emails.
- Throttling/digests for emails; quiet hours.
- SQLite mirror for faster queries while keeping CSV source of truth.
- 3D improvements: contact visualization heatmaps, clearance maps, basic interference resolution hints.
- PowerPoint export automation for managers’ decks.
- Per-project custom fields and templates.

---

### 29) Quick Start Checklist (for the first run)
1. Create `C:\TFApp\projects.csv` with at least one row (e.g., `TF10,C:\TF10_DemoRoot\,true`).
2. In `C:\TF10_DemoRoot\`, create subfolders: `Database`, `CAD\Parts`, `Analysis`, `Reports`, `Locks`, `Temp`.
3. Initialize empty CSVs with the headers above inside `Database\`.
4. Run the app; set Admin username/password when prompted.
5. Add users and parts; assign owner for each part.
6. Designers can ingest a STEP with `_nnn` suffix, add notes + PPT, then activate.
7. Analysts create analyses, add notes/load cases, and move statuses.

---

This document is self-contained and can be used as a prompt/spec in any environment to implement the application exactly as agreed.