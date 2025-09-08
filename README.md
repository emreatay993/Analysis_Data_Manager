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
