# Project Delivery Management

A working two-role delivery application: Delivery Managers record project information, the Delivery Head reviews what changed and approves or returns it.

Node.js only — **no npm packages, no build step, no database**. All persistence is JSON files.

---

## How to run

```bash
cd project-delivery-management
node seed.js      # creates data/users.json, data/projects.json, data/auditLog.json
node server.js    # http://localhost:3000
```

or `npm run seed` and `npm start`. Node 18 or later. `PORT=8080 node server.js` to change the port.

To verify everything end to end, leave the server running and in a second terminal:

```bash
node test-workflow.js
```

Re-running `node seed.js` resets all data to the starting state.

## Two builds, one repo

| Build | Files | Use it for |
|---|---|---|
| **Node** (default) | `server.js`, `public/`, `shared/fieldConfig.js` | The fuller UI — every section on one page, sticky action bar. Runs locally or on any Node host. |
| **Streamlit** | `streamlit_app.py`, `field_config.py`, `store.py`, `seed_data.py` | The public demo link. `pip install -r requirements.txt && streamlit run streamlit_app.py` |

Both read the same field configuration (584 fields, 10 sections) and the same JSON storage layout, and both enforce the same workflow and permissions. **DEPLOY.md** covers GitHub + Streamlit Community Cloud.

## Login credentials

| Username | Password | Role | Sees |
|---|---|---|---|
| `manager1` | `manager123` | Delivery Manager (DM001) | P001–P004 |
| `manager2` | `manager123` | Delivery Manager (DM002) | P005–P007 |
| `manager3` | `manager123` | Delivery Manager (DM003) | P008–P010 |
| `head1` | `head123` | Delivery Head (DH001) | All 10 projects |

Prototype credentials only — passwords are stored in plain text in `data/users.json`.

---

## What to click through

**As `manager1`:** open **P001** (Draft) → edit any text boxes → **Save draft** → **Submit for review**.
Open **P003** to see a rejected project with the Delivery Head's comments, correct it and resubmit.

**As `head1`:** the dashboard lists all ten projects with per-manager filters. Open **P005** — it has been submitted twice, so the *What changed since the previous submission* table shows four changed fields. Then **Approve** or **Reject** (a reason is mandatory).

---

## Where the fields came from

The workbook `Fixed_Priced_POC_Template.xlsx` was inspected once, during development. Its sheets, sections, row labels and column order were transcribed into a single configuration file, `shared/fieldConfig.js`. The workbook is not part of the application and is never read at runtime.

```
Fixed_Priced_POC_Template.xlsx
        ↓  (inspected during development)
shared/fieldConfig.js      ← 10 sections, 584 fields
        ↓  (rendered dynamically)
Project Edit screen        ← 584 <input type="text">
        ↓
data/projects.json
        ↓
Delivery Head review → Approve / Reject
```

`FIELDS.md` lists every extracted field, section by section.

| Source sheet | Contributes |
|---|---|
| `README` | Nothing — it is the workbook's own guidance sheet |
| `Baseline - GPE` | Baseline project details, Resource Loading, Efforts, Revenue Accrual summary, Accrued Revenue |
| `Project Financials` | Milestones vs Invoiced, Revenue Accrual view |
| `Level wise ResourcePplanning` | FTE Planned / Actual / Anticipated, level wise (T1–T9) |

The monthwise blocks carry the workbook's twelve month columns (Mar-2026 → Feb-2027) plus its TOTAL column. To add or remove a month or a level, edit the `MONTHS` or `levelRows` definition in `shared/fieldConfig.js` — nothing else changes.

---

## Confirmations against the brief

1. **Every extracted field is present on the Edit screen.** All 584 fields render from `FIELD_CONFIG.SECTIONS`; the test asserts each project record holds all 584 ids (`test-workflow.js`, section 2).
2. **Every field is a text input.** `textBox()` in `public/app.js` is the only field renderer in the application and emits `<input type="text">`. There are no date pickers, dropdowns, checkboxes, radio buttons, numeric spinners or editable grid components anywhere in the field area. Monthwise fields are laid out in a labelled row/column arrangement so the month each box belongs to is readable — each cell is still an ordinary text box, and each carries an accessible label such as *Efforts Actual — Jun-2026*.
3. **No Excel upload.** The application has no file input, no upload endpoint and no import route. `grep -ri "upload\|multipart\|xlsx" server.js public/` returns nothing.
4. **No database.** No SQL, MongoDB, SQLite, Firebase or Supabase; no ORM; no external packages at all. `package.json` has no dependencies.
5. **Field order preserved.** Sections and rows appear in workbook order: baseline details → resource loading → efforts → accrual summary → accrued revenue → milestones → accrual view → the three level-wise blocks.

## JSON storage structure

```
data/
├── users.json      { users: [ { id, username, password, name, role, projectIds } ] }
├── projects.json   { projects: [ … ] }
└── auditLog.json   { entries: [ { projectId, action, performedBy, detail, timestamp } ] }
```

A project record:

```json
{
  "id": "P001",
  "name": "Atlas Core Migration",
  "client": "ABC Industries",
  "projectStatus": "Active",
  "deliveryManagerId": "DM001",
  "approvalStatus": "DRAFT",
  "fields": { "baselineInfo__projectCode": "PRJ-1001", "efforts__effortsActual__m2026_06": "1100" },
  "currentSubmittedFields": null,
  "previousSubmittedFields": null,
  "submissionCount": 0,
  "submittedBy": null,  "submittedAt": null,
  "approvedBy": null,   "approvedAt": null,
  "rejectedBy": null,   "rejectedAt": null,
  "rejectionReason": null,
  "lastUpdated": "2026-08-01T10:00:00.000Z",
  "lastUpdatedBy": "DM001"
}
```

`fields` holds all 584 workbook-derived values. `currentSubmittedFields` and `previousSubmittedFields` are snapshots taken at submission time — the Delivery Head's change table is the difference between them, and it only appears once a second submission exists.

Writes go to a temporary file and are renamed into place, so an interrupted save cannot leave a half-written JSON file.

## Approval states

```
DRAFT ──save──▶ DRAFT ──submit──▶ SUBMITTED ──approve──▶ APPROVED (locked)
                                       │
                                    reject (reason mandatory)
                                       ▼
                                   REJECTED ──edit, save, submit──▶ SUBMITTED
```

A submitted or approved project rejects edits at the API level, not just in the UI.

## Permissions

| | Delivery Manager | Delivery Head |
|---|---|---|
| See own projects | yes | — |
| See all projects | no (403) | yes |
| Edit / save / submit | own projects, when DRAFT or REJECTED | no (403) |
| Approve / reject | no (403) | submitted projects only |
| Full audit history | own project's history | all (403 for managers) |

Enforced in `server.js` on every request; the UI simply reflects it.

## Files

```
project-delivery-management/
├── server.js                 API + static server (Node core modules only)
├── seed.js                   Creates the JSON data files
├── test-workflow.js          49-check end-to-end workflow test
├── package.json              No dependencies
├── FIELDS.md                 Every field extracted from the workbook
├── shared/fieldConfig.js     The single field configuration (server + browser)
├── public/index.html
├── public/app.js             Views, dynamic field rendering, actions
├── public/styles.css
└── data/                     users.json · projects.json · auditLog.json
```

## API

| Method | Path | Who |
|---|---|---|
| POST | `/api/login` · `/api/logout` · GET `/api/me` | anyone / signed in |
| GET | `/api/projects` | role-scoped list, counts, manager filter list |
| GET | `/api/projects/:id` | project, change comparison, history, `canEdit` |
| PUT | `/api/projects/:id/fields` | owning manager, DRAFT or REJECTED |
| POST | `/api/projects/:id/submit` | owning manager |
| POST | `/api/projects/:id/approve` · `/reject` | Delivery Head, submitted only |
| GET | `/api/audit` | Delivery Head |

Sessions are bearer tokens held in server memory, so restarting the server signs everyone out. Project data is unaffected.
