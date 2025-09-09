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
