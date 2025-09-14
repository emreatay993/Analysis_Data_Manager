# TF Engineering Data Manager (Sprint 1)

Windows PyQt5 desktop app to manage parts/revisions and analyses using CSV files in configurable project roots.

## Quick start

1. Create projects registry file:
   - Path: `C:\TFApp\projects.csv`
   - Example content:
     ```
     TF10,C:\TF10_DemoRoot\,true
     TF35,C:\TF35_DemoRoot\,true
     ```
2. Create the folders under the chosen project root (e.g., `C:\TF10_DemoRoot\`):
   `Database`, `CAD\\Parts`, `Analysis`, `Reports`, `Locks`, `Temp`.
3. Run the app:
   ```bash
   python -m app.main
   ```

Sprint 1 delivers: project switcher, CSV layer with locks, Admin basics, Parts/Revisions UI with owner-only activation and required notes/PPT, basic analysis creation, and Outlook notifications for activation and analysis creation.

---

## Sprint 2 additions
- Analysis lifecycle UI: status change with validation; presentation number required for `presented`.
- Reassignment flow: change analyst with mandatory notes.
- Load case creation: add load cases with mandatory notes.
- Status history recording in `status_history.csv`.
- Email notifications for analysis creation and key status changes (`results are ready for evaluation`, `presented`).
- Excel export for managers: saves project summary to `Reports/<PROJECT>_summary.xlsx`.

## Sprint 2 acceptance test checklist
1. Create an analysis (Analyses tab → Create). Provide notes.
   - Expected: Row in `analyses.csv`; folder created under `Analysis/<part>/<analysis_id>/`; note in `analysis_event_notes.csv`.
2. Reassign the analysis (Reassign). Provide notes.
   - Expected: `analyses.csv.analyst` updates; note row with `event_type=reassigned`.
3. Add a load case (Add Load Case). Provide notes.
   - Expected: Row in `load_cases.csv` and note with `event_type=new_load_case`.
4. Change status to `results are ready for evaluation` and then to `presented` (fill Presentation #).
   - Expected: `analyses.csv.status` updates; `presentation_number` stored; entries appended to `status_history.csv`.
5. Export to Excel (Export to Excel button).
   - Expected: File written to `Reports/<PROJECT>_summary.xlsx` with sheets: parts, revisions, analyses, status_history.
6. Project isolation: Switch to another project and ensure lists are independent; return and verify original project’s data remains intact.

---

## Sprint 3 additions
- Assemblies management: create assemblies, add/remove members (part + revision).
- Contacts calculation: compute pair pairs and classify (stub now; OCC integration planned).
- Assemblies tab integrated into the main UI.

## Sprint 3 acceptance test checklist
1. Create an assembly (Assemblies tab → New Assembly) with an ID.
   - Expected: Row in `assemblies.csv` appears.
2. Add two or more members (Add Member) with valid `part_base` and `rev_index`.
   - Expected: Rows in `assembly_members.csv` with `included=true`.
3. Compute contacts (Compute Contacts).
   - Expected: Rows in `contacts.csv` for each pair; visible in the bottom table.
4. Project isolation: Switch projects and confirm assemblies/members/contacts are independent per project.

---

## Sprint 4 additions
- Auto-ingest watcher: detects new/modified STEP and PPT files under `CAD/` and refreshes the UI.
- Auto-refresh: periodic timer updates tables without manual actions.
- Filters: quick text filters for Parts (part, owner) and Analyses (part, status, analyst).
- Logging: rotating file log at `%APPDATA%/TFApp/logs/app.log`.

## Sprint 4 acceptance test checklist
1. Auto-ingest
   - Drop a new STEP (e.g., `PART_002.step`) into `CAD\Parts\<part>\rev_002\`.
   - Expected: Within a few seconds, `revisions.csv` gains the row with `pending_activation=true` and the Parts view shows updated latest rev.
2. PPT detection
   - Place/modify `Change_Presentation.pptx` under a revision folder.
   - Expected: Parts view “PPT Exists?” updates after a few seconds.
3. Auto-refresh
   - Without clicking refresh, edit a CSV externally (e.g., change an analyst in `analyses.csv`).
   - Expected: Table reflects change within the refresh interval.
4. Filters
   - Type in the Parts and Analyses filter bars.
   - Expected: Rows filter live by the entered text.
5. Logging
   - Open `%APPDATA%/TFApp/logs/app.log`.
   - Expected: File exists; future warnings/info will appear here.

---

## OCC setup (Windows)
- Preferred: `cadquery-ocp` (provides `OCP.*` bindings)
  ```powershell
  python -m pip install --upgrade pip setuptools wheel
  python -m pip install cadquery-ocp
  python -c "from OCP.STEPControl import STEPControl_Reader; print('OCP OK')"
  ```
- Alternative: `OCP` (wraps platform wheel)
  ```powershell
  python -m pip install OCP
  python -c "from OCP.BRepExtrema import BRepExtrema_DistShapeShape; print('OCP Dist OK')"
  ```
- If using conda and prefer `pythonocc-core`:
  ```powershell
  conda create -n occ310 python=3.10 -y
  conda activate occ310
  conda install -c conda-forge pythonocc-core=7.7.* -y
  python -c "from OCC.Core.STEPControl import STEPControl_Reader; print('pythonocc OK')"
  ```
- Requirements: 64‑bit Python, Microsoft Visual C++ 2015–2022 (x64) redistributable.

---

## OCC-based contacts and viewer (current step)
- Distances: compute min gaps via OCC (OCP/pythonocc-core). Classification:
  - penetration: common volume > 1e-6 mm³ → `min_gap_mm = -0.002`
  - touching: |gap| ≤ 0.002 mm and negligible common volume
  - clearance: 0.002 < gap ≤ 5.0 mm
  - omitted: gap > 5.0 mm (not listed)
- Assemblies tab: button “Compute Contacts (OCC)” stores measured gaps in `contacts.csv`.
- Viewer (planned next): embed OCC viewer and highlight pairs when selecting a contact row.

### Acceptance checklist (OCC distances)
1. Ensure OCC is available (see OCC setup above).
2. Ingest STEP files so `revisions.csv.step_path` is populated.
3. Add at least two members to an assembly and press “Compute Contacts (OCC)”.
   - Expected: `contacts.csv` updates with numeric `min_gap_mm` and a `relation` per pair.
   - Expected: pairs with clearance > 5 mm are not listed.
4. Switch projects and repeat; contacts remain isolated per project.
