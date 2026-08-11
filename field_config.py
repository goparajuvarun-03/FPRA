"""Centralized field configuration.

Every field was extracted, during development, from the reference workbook
"Fixed_Priced_POC_Template.xlsx". The workbook is NOT read at runtime and is
NOT part of the deployed application. This module is the single source of
truth for the Project Edit screen, the Review screen and the change table.

This is the Python twin of shared/fieldConfig.js (used by the Node build).
Both are generated from the same inspection of the workbook.
"""

MONTHS = [
    {"key": "m2026_03", "label": "Mar-2026", "source_date": "25-Mar-2026"},
    {"key": "m2026_04", "label": "Apr-2026", "source_date": "26-Apr-2026"},
    {"key": "m2026_05", "label": "May-2026", "source_date": "27-May-2026"},
    {"key": "m2026_06", "label": "Jun-2026", "source_date": "27-Jun-2026"},
    {"key": "m2026_07", "label": "Jul-2026", "source_date": "28-Jul-2026"},
    {"key": "m2026_08", "label": "Aug-2026", "source_date": "28-Aug-2026"},
    {"key": "m2026_09", "label": "Sep-2026", "source_date": "28-Sep-2026"},
    {"key": "m2026_10", "label": "Oct-2026", "source_date": "29-Oct-2026"},
    {"key": "m2026_11", "label": "Nov-2026", "source_date": "29-Nov-2026"},
    {"key": "m2026_12", "label": "Dec-2026", "source_date": "30-Dec-2026"},
    {"key": "m2027_01", "label": "Jan-2027", "source_date": "30-Jan-2027"},
    {"key": "m2027_02", "label": "Feb-2027", "source_date": "02-Feb-2027"},
]

COLUMNS = [{"key": "total", "label": "TOTAL"}] + MONTHS


def _level_rows(total_label):
    return [{"id": "total", "label": total_label}] + [
        {"id": "T%d" % i, "label": "T%d" % i} for i in range(1, 10)
    ]


SECTIONS = [
    # ---- Sheet: Baseline - GPE ----
    {
        "id": "baselineInfo",
        "sheet": "Baseline - GPE",
        "title": "Section I: Project Details — Project Baseline Information as per GPE",
        "note": "Entered once at the start of the project, on the basis of the approved GPE.",
        "layout": "stack",
        "fields": [
            {"id": "projectCode", "label": "Project Code"},
            {"id": "projectName", "label": "Project Name"},
            {"id": "startDate", "label": "Start Date"},
            {"id": "endDate", "label": "End Date"},
            {"id": "tcv", "label": "TCV"},
            {"id": "soldMarginPct", "label": "Sold Margin%"},
            {"id": "totalBudgetedEfforts", "label": "Total Budgeted Efforts"},
        ],
    },
    {
        "id": "resourceLoading",
        "sheet": "Baseline - GPE",
        "title": "Resource Loading (FTE Loading)",
        "note": "Monthwise FTE loading. Totals are summarised from the level-wise resource planning section.",
        "layout": "matrix",
        "rows": [
            {"id": "resourcesPlannedGPE", "label": "Resources Planned as per GPE"},
            {"id": "resourcesActual", "label": "Resources Actual"},
            {"id": "resourcesAnticipated", "label": "Resources Anticipated to Complete"},
        ],
    },
    {
        "id": "efforts",
        "sheet": "Baseline - GPE",
        "title": "Efforts (in Hrs) Planned / Consumed",
        "note": "Efforts Actual is updated every month from e360 timesheets for the current month only. "
                "Remaining Efforts Anticipated to Complete is entered for future months only.",
        "layout": "matrix",
        "rows": [
            {"id": "effortsPlannedGPE", "label": "Efforts Planned as per GPE"},
            {"id": "effortsActual", "label": "Efforts Actual"},
            {"id": "remainingEffortsAnticipated", "label": "Remaining Efforts Anticipated to Complete"},
        ],
    },
    {
        "id": "accrualSummary",
        "sheet": "Baseline - GPE",
        "title": "Section II: Revenue Accrual — Summary",
        "note": "In the source template these are calculated cells. A red flag on Total Efforts To Completion "
                "means a project effort overrun that needs re-baselining approval.",
        "layout": "stack",
        "fields": [
            {"id": "tcv", "label": "TCV"},
            {"id": "totalBudgetedEfforts", "label": "Total Budgeted Efforts"},
            {"id": "totalEffortsActual", "label": "Total Efforts Actual"},
            {"id": "remainingEffortsAnticipated", "label": "Remaining Efforts Anticipated to Complete"},
            {"id": "totalEffortsToCompletion", "label": "Total Efforts To Completion"},
        ],
    },
    {
        "id": "accruedRevenue",
        "sheet": "Baseline - GPE",
        "title": "Section II: Revenue Accrual — Accrued Revenue",
        "layout": "matrix",
        "rows": [
            {"id": "accruedForecast", "label": "Accrued Forecast"},
            {"id": "accruedActual", "label": "Accrued Actual"},
            {"id": "accrualAnticipated", "label": "Accrual Anticipated to Complete"},
        ],
    },
    # ---- Sheet: Project Financials ----
    {
        "id": "milestones",
        "sheet": "Project Financials",
        "title": "Section I: Milestone Details as per GPE Vs Invoiced Amounts",
        "note": "Payment milestones by month from the contract; invoiced amounts are entered as and when an invoice is raised.",
        "layout": "matrix",
        "rows": [
            {"id": "milestoneAmounts", "label": "Milestone Amounts"},
            {"id": "invoicedTillDate", "label": "Invoiced Till Date"},
        ],
    },
    {
        "id": "financialsAccrual",
        "sheet": "Project Financials",
        "title": "Section II: Revenue Accrual View",
        "note": "In the source template this view is displayed from the Baseline tab.",
        "layout": "matrix",
        "rows": [
            {"id": "accruedForecast", "label": "Accrued Forecast"},
            {"id": "accruedActual", "label": "Accrued Actual"},
            {"id": "accrualAnticipated", "label": "Accrual Anticipated to Complete"},
        ],
    },
    # ---- Sheet: Level wise Resource Planning ----
    {
        "id": "levelPlanned",
        "sheet": "Level wise Resource Planning",
        "title": "FTE Loading — Resources Planned as per GPE (Level wise)",
        "layout": "matrix",
        "rows": _level_rows("Resources Planned as per GPE"),
    },
    {
        "id": "levelActual",
        "sheet": "Level wise Resource Planning",
        "title": "FTE Loading — Resources Actual (Level wise)",
        "note": "Updated every month from e360 allocations for the current month only.",
        "layout": "matrix",
        "rows": _level_rows("Resources Actual"),
    },
    {
        "id": "levelAnticipated",
        "sheet": "Level wise Resource Planning",
        "title": "FTE Loading — Resources Anticipated to Complete (Level wise)",
        "note": "Values are entered for future months only.",
        "layout": "matrix",
        "rows": _level_rows("Resources Anticipated to Complete"),
    },
]


def _build_fields():
    out = []
    for section in SECTIONS:
        if section["layout"] == "stack":
            for f in section["fields"]:
                out.append({
                    "id": "%s__%s" % (section["id"], f["id"]),
                    "label": f["label"],
                    "section": section["title"],
                    "section_id": section["id"],
                    "sheet": section["sheet"],
                })
        else:
            for row in section["rows"]:
                for col in COLUMNS:
                    out.append({
                        "id": "%s__%s__%s" % (section["id"], row["id"], col["key"]),
                        "label": "%s — %s" % (row["label"], col["label"]),
                        "section": section["title"],
                        "section_id": section["id"],
                        "sheet": section["sheet"],
                        "row_id": row["id"],
                        "column_key": col["key"],
                    })
    return out


FIELDS = _build_fields()
FIELD_BY_ID = {f["id"]: f for f in FIELDS}
FIELD_COUNT = len(FIELDS)
