"""Builds data/users.json, data/projects.json and data/auditLog.json.

Run directly (`python seed_data.py`) to reset the demo data, or let the app
call build() automatically on first run.
"""

import json
import os
from datetime import datetime, timedelta, timezone

import field_config as CFG

MONTH_KEYS = [m["key"] for m in CFG.MONTHS]

USERS = {
    "users": [
        {"id": "DM001", "username": "manager1", "password": "manager123", "name": "Manager One",
         "role": "DELIVERY_MANAGER", "projectIds": ["P001", "P002", "P003", "P004"]},
        {"id": "DM002", "username": "manager2", "password": "manager123", "name": "Manager Two",
         "role": "DELIVERY_MANAGER", "projectIds": ["P005", "P006", "P007"]},
        {"id": "DM003", "username": "manager3", "password": "manager123", "name": "Manager Three",
         "role": "DELIVERY_MANAGER", "projectIds": ["P008", "P009", "P010"]},
        {"id": "DH001", "username": "head1", "password": "head123", "name": "Delivery Head",
         "role": "DELIVERY_HEAD"},
    ]
}

SPEC = [
    {"id": "P001", "name": "Atlas Core Migration", "client": "ABC Industries", "dm": "DM001",
     "status": "DRAFT", "projectStatus": "Active", "full": True},
    {"id": "P002", "name": "Orion Payments Platform", "client": "XYZ Corporation", "dm": "DM001",
     "status": "SUBMITTED", "projectStatus": "Active", "full": True},
    {"id": "P003", "name": "Helix Data Warehouse", "client": "DEF Technologies", "dm": "DM001",
     "status": "REJECTED", "projectStatus": "Active", "full": True,
     "reason": "Efforts Actual for Jun-2026 does not tie back to the e360 timesheet extract. Please correct and resubmit."},
    {"id": "P004", "name": "Beacon Field Services App", "client": "Northwind Retail", "dm": "DM001",
     "status": "DRAFT", "projectStatus": "Planning", "full": False},
    {"id": "P005", "name": "Vertex Claims Automation", "client": "Sterling Insurance", "dm": "DM002",
     "status": "SUBMITTED", "projectStatus": "Active", "full": True},
    {"id": "P006", "name": "Cobalt Network Refresh", "client": "Meridian Telecom", "dm": "DM002",
     "status": "APPROVED", "projectStatus": "Active", "full": True},
    {"id": "P007", "name": "Juniper HR Transformation", "client": "Cascade Foods", "dm": "DM002",
     "status": "DRAFT", "projectStatus": "Planning", "full": False},
    {"id": "P008", "name": "Quarry Logistics Control Tower", "client": "Ironbridge Mining", "dm": "DM003",
     "status": "SUBMITTED", "projectStatus": "Active", "full": True},
    {"id": "P009", "name": "Lumen Customer Portal", "client": "Harbour Bank", "dm": "DM003",
     "status": "APPROVED", "projectStatus": "Active", "full": True},
    {"id": "P010", "name": "Sable Regulatory Reporting", "client": "Harbour Bank", "dm": "DM003",
     "status": "REJECTED", "projectStatus": "On Hold", "full": True,
     "reason": "Milestone Amounts total does not match the TCV entered in the baseline section."},
]


def _blank():
    return {f["id"]: "" for f in CFG.FIELDS}


def _row(fields, section_id, row_id, values):
    total = 0
    for i, v in enumerate(values):
        if i >= len(MONTH_KEYS) or v == "" or v is None:
            continue
        fields["%s__%s__%s" % (section_id, row_id, MONTH_KEYS[i])] = str(v)
        total += v
    fields["%s__%s__total" % (section_id, row_id)] = str(total)


def _sample(code, name, tcv):
    f = _blank()
    f["baselineInfo__projectCode"] = code
    f["baselineInfo__projectName"] = name
    f["baselineInfo__startDate"] = "01-Jan-2026"
    f["baselineInfo__endDate"] = "31-Dec-2026"
    f["baselineInfo__tcv"] = str(tcv)
    f["baselineInfo__soldMarginPct"] = "32"
    f["baselineInfo__totalBudgetedEfforts"] = "12000"

    _row(f, "resourceLoading", "resourcesPlannedGPE", [10, 10, 10, 15, 15, 15, 15, 10, 10, 8, 8, 8])
    _row(f, "resourceLoading", "resourcesActual", [8, 10, 10, 16, 0, 0, 0, 0, 0, 0, 0, 0])
    _row(f, "resourceLoading", "resourcesAnticipated", [0, 0, 0, 0, 16, 16, 16, 10, 10, 8, 8, 8])

    _row(f, "efforts", "effortsPlannedGPE", [1000] * 12)
    _row(f, "efforts", "effortsActual", [800, 1000, 1100, 1100])
    _row(f, "efforts", "remainingEffortsAnticipated", ["", "", "", "", 1100, 1000, 1200, 1000, 1200, 1000, 1000, 800])

    f["accrualSummary__tcv"] = str(tcv)
    f["accrualSummary__totalBudgetedEfforts"] = "12000"
    f["accrualSummary__totalEffortsActual"] = "4000"
    f["accrualSummary__remainingEffortsAnticipated"] = "8300"
    f["accrualSummary__totalEffortsToCompletion"] = "12300"

    for sec in ("accruedRevenue", "financialsAccrual"):
        _row(f, sec, "accruedForecast", [100000] * 12)
        _row(f, sec, "accruedActual", [80000, 100000, 110000, 110000, 0, 0, 0, 0, 0, 0, 0, 0])
        _row(f, sec, "accrualAnticipated", [0, 0, 0, 0, 106024, 96386, 115663, 96386, 115663, 96386, 96386, 77108])

    _row(f, "milestones", "milestoneAmounts", [10000, "", 220000, "", "", 250000, 250000, "", "", 220000, "", 250000])
    _row(f, "milestones", "invoicedTillDate", [10000, "", "", 220000])

    _row(f, "levelPlanned", "T1", [3, 3, 3, 5, 5, 5, 5, 3, 3, 3, 3, 3])
    _row(f, "levelPlanned", "T2", [3, 3, 3, 6, 6, 6, 6, 3, 3, 3, 3, 3])
    _row(f, "levelPlanned", "T3", [1, 1, 1, 1, 1, 1, 1, 1, 1])
    _row(f, "levelPlanned", "T4", [1] * 12)
    _row(f, "levelPlanned", "T5", [1, 1, 1, 1, 1, 1, 1, 1, 1])
    _row(f, "levelPlanned", "T6", [1] * 12)
    _row(f, "levelPlanned", "total", [10, 10, 10, 15, 15, 15, 15, 10, 10, 8, 8, 8])

    _row(f, "levelActual", "T1", [1, 3, 3, 5])
    _row(f, "levelActual", "T2", [3, 3, 3, 6])
    _row(f, "levelActual", "T3", [1, 1, 1, 2])
    _row(f, "levelActual", "T4", [1, 1, 1, 1])
    _row(f, "levelActual", "T5", [1, 1, 1, 1])
    _row(f, "levelActual", "T6", [1, 1, 1, 1])
    _row(f, "levelActual", "total", [8, 10, 10, 16, 0, 0, 0, 0, 0, 0, 0, 0])

    _row(f, "levelAnticipated", "T1", ["", "", "", "", 5, 5, 5, 3, 3, 3, 3, 3])
    _row(f, "levelAnticipated", "T2", ["", "", "", "", 6, 6, 6, 3, 3, 3, 3, 3])
    _row(f, "levelAnticipated", "T3", ["", "", "", "", 2, 2, 2, 1, 1])
    _row(f, "levelAnticipated", "T4", ["", "", "", "", 1, 1, 1, 1, 1, 1, 1, 1])
    _row(f, "levelAnticipated", "T5", ["", "", "", "", 1, 1, 1, 1, 1])
    _row(f, "levelAnticipated", "T6", ["", "", "", "", 1, 1, 1, 1, 1, 1, 1, 1])
    _row(f, "levelAnticipated", "total", [0, 0, 0, 0, 16, 16, 16, 10, 10, 8, 8, 8])
    return f


def _starter(code, name, tcv):
    f = _blank()
    f["baselineInfo__projectCode"] = code
    f["baselineInfo__projectName"] = name
    f["baselineInfo__startDate"] = "01-Apr-2026"
    f["baselineInfo__endDate"] = "31-Mar-2027"
    f["baselineInfo__tcv"] = str(tcv)
    return f


def build(data_dir):
    os.makedirs(data_dir, exist_ok=True)
    base = datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc)
    counter = {"n": 0}

    def ts():
        counter["n"] += 1
        return (base + timedelta(hours=counter["n"])).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    entries = []

    def log(pid, action, by, detail, when):
        entries.append({"projectId": pid, "action": action, "performedBy": by,
                        "detail": detail, "timestamp": when})

    projects = []
    for idx, s in enumerate(SPEC):
        code = "PRJ-%d" % (1001 + idx)
        fields = _sample(code, s["name"], 900000 + idx * 150000) if s["full"] \
            else _starter(code, s["name"], 450000 + idx * 25000)
        created = ts()
        p = {
            "id": s["id"], "name": s["name"], "client": s["client"],
            "projectStatus": s["projectStatus"], "deliveryManagerId": s["dm"],
            "approvalStatus": "DRAFT", "fields": fields,
            "currentSubmittedFields": None, "previousSubmittedFields": None,
            "submissionCount": 0, "submittedBy": None, "submittedAt": None,
            "approvedBy": None, "approvedAt": None, "rejectedBy": None,
            "rejectedAt": None, "rejectionReason": None,
            "lastUpdated": created, "lastUpdatedBy": s["dm"],
        }
        log(p["id"], "CREATED", s["dm"], "Project created", created)

        if s["status"] != "DRAFT":
            p["currentSubmittedFields"] = dict(fields)
            p["submissionCount"] = 1
            p["submittedBy"] = s["dm"]
            p["submittedAt"] = ts()
            p["approvalStatus"] = "SUBMITTED"
            p["lastUpdated"] = p["submittedAt"]
            log(p["id"], "SUBMITTED", s["dm"], "Submission #1", p["submittedAt"])

            if s["status"] == "APPROVED":
                p["approvalStatus"] = "APPROVED"
                p["approvedBy"] = "DH001"
                p["approvedAt"] = ts()
                p["lastUpdated"] = p["approvedAt"]
                log(p["id"], "APPROVED", "DH001", None, p["approvedAt"])
            elif s["status"] == "REJECTED":
                p["approvalStatus"] = "REJECTED"
                p["rejectedBy"] = "DH001"
                p["rejectedAt"] = ts()
                p["rejectionReason"] = s["reason"]
                p["lastUpdated"] = p["rejectedAt"]
                log(p["id"], "REJECTED", "DH001", s["reason"], p["rejectedAt"])
        projects.append(p)

    # P005 carries a second submission so the Delivery Head has a real change set to review.
    p5 = next(p for p in projects if p["id"] == "P005")
    p5["previousSubmittedFields"] = dict(p5["currentSubmittedFields"])
    p5["fields"]["baselineInfo__endDate"] = "31-Mar-2027"
    p5["fields"]["accrualSummary__totalEffortsToCompletion"] = "12800"
    p5["fields"]["efforts__effortsActual__m2026_06"] = "1250"
    p5["fields"]["milestones__milestoneAmounts__m2026_08"] = "275000"
    p5["currentSubmittedFields"] = dict(p5["fields"])
    p5["submissionCount"] = 2
    p5["submittedAt"] = ts()
    p5["lastUpdated"] = p5["submittedAt"]
    log(p5["id"], "RESUBMITTED", p5["deliveryManagerId"], "Submission #2", p5["submittedAt"])

    def dump(name, obj):
        with open(os.path.join(data_dir, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2)

    dump("users.json", USERS)
    dump("projects.json", {"projects": projects})
    dump("auditLog.json", {"entries": entries})
    return len(projects), len(entries)


if __name__ == "__main__":
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    n_p, n_a = build(here)
    print("Seeded %d projects, %d users, %d audit entries." % (n_p, len(USERS["users"]), n_a))
    print("Each project carries %d configured fields." % CFG.FIELD_COUNT)
