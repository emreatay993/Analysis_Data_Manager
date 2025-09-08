## TF Engineering Data Manager — Manager-Friendly Plan (v1)

Audience: Design Managers, Design Engineers, Analysts, Program/Project Managers  
Goal: Agree on scope, value, timelines, and decision points before build starts.

---

### Executive summary
- **Problem**: Part revisions, analyses, and handoffs live in many folders and emails; status and traceability are hard to see quickly.
- **Solution**: A Windows desktop app (PyQt5) that organizes parts, revisions, analyses, assemblies, and notifications across multiple projects, storing data in simple CSV files in project folders.
- **Outcome**: Faster reviews, fewer handoff mistakes, full traceability (who changed what/when), and exportable status for leadership.

---

### Who benefits and how
- **Design engineers**: One place to upload new CAD revisions, capture “What changed/Why/Impacts,” and control activation of their parts.
- **Analysts**: Clear view of analyses by status, quick creation/reassignment with notes, and alerts at key milestones.
- **Managers**: Read-only dashboards and Excel exports; automatic CC on critical milestones.
- **Everyone**: Consistent project structure; searchable history with audit trail.

---

### What’s in scope (v1)
- **Multi-project support** with a simple registry: e.g., `TF10` → `C:\TF10_DemoRoot\`, `TF35` → `C:\TF35_DemoRoot\`.
- **Parts & revisions**:
  - Revisions detected from file names (`_001`, `_002`, …).
  - Designers must add notes (What/Why/Impacts) and a PPT per revision.
  - Only the part owner can activate a revision.
- **Analyses**:
  - Create/reassign with required notes; add load cases with notes.
  - Track statuses from approval to “presented/archived.”
  - Optional free-form tags for search.
- **Assemblies**:
  - Visualize supplied STEP files (already in engine coordinates).
  - Detect touching/penetration with the agreed tolerance (±0.002 mm).
- **Notifications (Outlook)**:
  - New revision (pending), analysis created/reassigned, results ready, presented (with presentation number), new load case.
  - CC part manager at “results ready” and “presented.”
- **Exports**: Excel from any table/filter.
- **Audit**: Every change logged to an events file.

Out of scope (for now): internet services, external databases, advanced meshing, automated CAD transforms.

---

### How it will change the way we work
- **Standardized project folders** across programs; consistent CSV “mini-database” in each project’s `Database` folder.
- **Mandatory revision context** (notes + PPT) before a revision can go live.
- **Clear roles**: designers own part activation; analysts own analysis lifecycle.
- **Fewer emails to remember**: system sends the essentials at the right time.
- **Managers see real-time status** and can export directly to Excel.

---

### Key user workflows
- **Designer**
  - Drops new STEP with `_nnn` suffix → app detects it → fills “What/Why/Impacts” and adds PPT → activates the revision (owner only) → notification sent.
- **Analyst**
  - Creates analysis for a chosen revision, adds notes → updates statuses as work progresses → adds load cases with notes → marks “results ready,” later “presented” with presentation number → notifications sent.
- **Manager**
  - Opens dashboard, filters by project/owner/status → exports to Excel → automatically CC’d when results are ready/presented.
- **Admin**
  - Adds projects and seeds folders → manages users/roles → assigns parts to owners → can override in edge cases.

---

### Data and permissions in plain language
- **Projects**: Listed in a small registry file. Each project has its own folders and CSVs.
- **Parts**: Each part has exactly one owner (designer) at a time.
- **Revisions**: File name suffix (`_001`) is the revision number; new files become “pending” until owner activates. Notes + PPT are required.
- **Analyses**: Track status, notes, tags, and presentation number; can be tied to any revision (“pinned”), with a warning if a newer active revision exists.
- **Permissions**:
  - Designers edit their parts.
  - Analysts edit their analyses.
  - Managers are read-only.
  - Admin can modify anything.

---

### Notifications (what gets emailed)
- **New revision (pending)**: to part owner (reminder to complete notes/PPT and activate).
- **Analysis created/reassigned**: to assigned analyst, requester, and part owner.
- **Results are ready for evaluation**: to requester and part owner, CC part manager.
- **Presented**: to requester and part owner, CC part manager; presentation number is mandatory.
- **New load case added**: to requester and part owner.

No throttling/quiet hours/digests in v1 (can add later if needed).

---

### Assembly checks (simple and useful)
- Load selected parts’ STEP files (already positioned).
- Compute part-to-part proximity:
  - Touching if the minimum gap is within ±0.002 mm.
  - Penetration if overlap exceeds 0.002 mm.
- Show a table of contacts and highlight the pair in 3D.

---

### Success metrics (how we’ll know it’s working)
- **Cycle time**: Time from designer upload to analysis start (target: −30%).
- **Rework**: Number of analysis reruns due to using the wrong revision (target: −50%).
- **Visibility**: Managers can export an accurate status snapshot in under 2 minutes.
- **Compliance**: 100% revisions with notes + PPT; zero activations without them.
- **Adoption**: ≥80% of design/analysis changes initiated through the app by month 2.

---

### Timeline and milestones (proposed)
- **Sprint 1 (2–3 weeks)**: Projects setup, CSV layer, Parts/Revisions screen, owner-only activation, basic notifications, Admin basics.
- **Sprint 2 (2–3 weeks)**: Analyses screen, required notes, status flow with history, notifications for results/presented/load cases, Excel exports.
- **Sprint 3 (2–3 weeks)**: Assembly viewer and contact detection, save results to table, UI polish.
- **Sprint 4 (2 weeks)**: File watcher for new STEP/PPT, better filters/search, robustness, training materials.

Pilot after Sprint 2 in one project (e.g., TF10), then expand.

---

### Training and rollout
- 60–90 min live demo + hands-on for Designers and Analysts.
- One-page quick reference (revision rules, statuses, where files go).
- Short video clips for common tasks (activate revision, create analysis, export status).
- Pilot with 5–10 users → incorporate feedback → org-wide rollout.

---

### Risks and mitigations
- **Folder variability**: Standardize during project seeding; app enforces structure.
- **User resistance**: Keep the UI simple; minimize mandatory fields; provide fast exports; early pilot feedback.
- **File conflicts**: Use safe locking; retry logic; clear messages when a file is busy.
- **Email noise (future)**: If needed, add digest/quiet hours later.

---

### Decisions already made
- CSV-based per-project storage; Windows-only app.
- One owner per part; owner controls activation after notes + PPT.
- Statuses include “results are ready for evaluation” and “presented” (requires presentation number).
- CC part manager at results/presented.
- Assembly tolerance: touching ±0.002 mm; penetration beyond ±0.002 mm.
- Exports in Excel; no web dashboards in v1.
- Multi-project: registry at `C:\TFApp\projects.csv` (demo); can be moved to a shared path.

---

### Decision to validate (manager/design/analysis input welcome)
- **Manager CC mapping**: Default to the owner’s line manager from the users list, with an optional per-part override. OK?
- **Shown statuses**: Are the names clear for your teams? Any you want to add/remove?
- **Presentation number format**: Free text is fine—do you want a suggested pattern (e.g., TR-YYYY-####)?
- **Analysis pinned to a revision**: Keep the warning banner if the active revision advances? Offer “Rebase” action?

---

### What we need from each group
- **Managers**
  - Confirm CC rule and status names.
  - Nominate the first project for pilot and a small champion group.
- **Design engineers**
  - Confirm that “What changed/Why/Impacts” + PPT is feasible for every revision.
  - Validate that owners activating their own parts fits the process.
- **Analysts**
  - Confirm core statuses and that “results ready/presented” notifications are helpful.
  - Validate tags and load-case notes flow.

---

### High-level deliverables
- Desktop app (installer)
- Seeded project folders and empty CSVs per project
- User guide (PDF), quick reference sheet, and 3–5 short training clips
- Example Excel exports (status snapshot, analyses by part, contact table)
- Configuration files (projects registry, admin settings)

---

### Contact and governance
- Product owner: You (Admin in the app)
- Primary stakeholders: Manager of Design, Manager of Analysis
- Feedback cadence: Weekly check-in during build; pilot debrief after Sprint 2

---

If this plan looks right, we’ll circulate it for sign-off and begin Sprint 1.