"""JSON file storage and workflow rules. No database.

On Streamlit Community Cloud the container filesystem is ephemeral: data written
here survives while the app is running, and resets when the app restarts or
redeploys. That is fine for a demo. For durable storage, run the app on a host
with a persistent disk, or point DATA_DIR at a mounted volume.
"""

import json
import os
import shutil
from datetime import datetime, timezone

import field_config as CFG

DATA_DIR = os.environ.get("PDM_DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
USERS = os.path.join(DATA_DIR, "users.json")
PROJECTS = os.path.join(DATA_DIR, "projects.json")
AUDIT = os.path.join(DATA_DIR, "auditLog.json")


# ---------------- low level ----------------
def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    shutil.move(tmp, path)  # avoids leaving a half-written file behind


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


# ---------------- seeding ----------------
def ensure_data():
    """Create the JSON files on first run. Existing files are left alone."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if all(os.path.exists(p) for p in (USERS, PROJECTS, AUDIT)):
        return
    import seed_data
    seed_data.build(DATA_DIR)


def reset_data():
    import seed_data
    os.makedirs(DATA_DIR, exist_ok=True)
    seed_data.build(DATA_DIR)


# ---------------- reads ----------------
def users():
    return _read(USERS)["users"]


def user_by_id(uid):
    return next((u for u in users() if u["id"] == uid), None)


def user_name(uid):
    u = user_by_id(uid)
    return u["name"] if u else (uid or "—")


def authenticate(username, password):
    return next(
        (u for u in users() if u["username"] == username.strip() and u["password"] == password),
        None,
    )


def projects():
    return _read(PROJECTS)["projects"]


def projects_for(user):
    if user["role"] == "DELIVERY_HEAD":
        return projects()
    return [p for p in projects() if p["deliveryManagerId"] == user["id"]]


def project(project_id):
    return next((p for p in projects() if p["id"] == project_id), None)


def can_open(user, p):
    return user["role"] == "DELIVERY_HEAD" or p["deliveryManagerId"] == user["id"]


def can_edit(user, p):
    return (
        user["role"] == "DELIVERY_MANAGER"
        and p["deliveryManagerId"] == user["id"]
        and p["approvalStatus"] in ("DRAFT", "REJECTED")
    )


def audit_entries(project_id=None):
    entries = _read(AUDIT)["entries"]
    if project_id:
        entries = [e for e in entries if e["projectId"] == project_id]
    return list(reversed(entries))


def changes(p):
    """Current submission vs the one before it. Empty until a second submission exists."""
    prev = p.get("previousSubmittedFields")
    if not prev:
        return []
    curr = p.get("currentSubmittedFields") or p["fields"]
    out = []
    for f in CFG.FIELDS:
        a = (prev.get(f["id"]) or "").strip()
        b = (curr.get(f["id"]) or "").strip()
        if a != b:
            out.append({
                "field_id": f["id"], "label": f["label"], "sheet": f["sheet"],
                "previous": a, "new": b,
            })
    return out


# ---------------- writes ----------------
def _save_project(updated):
    store = _read(PROJECTS)
    for i, p in enumerate(store["projects"]):
        if p["id"] == updated["id"]:
            store["projects"][i] = updated
            break
    _write(PROJECTS, store)


def _log(project_id, action, performed_by, detail=None):
    store = _read(AUDIT)
    store["entries"].append({
        "projectId": project_id, "action": action, "performedBy": performed_by,
        "detail": detail, "timestamp": now(),
    })
    _write(AUDIT, store)


class Denied(Exception):
    pass


def save_draft(user, project_id, values):
    p = project(project_id)
    if not can_edit(user, p):
        raise Denied("This project can no longer be edited.")
    clean = {}
    for f in CFG.FIELDS:
        v = values.get(f["id"], p["fields"].get(f["id"], ""))
        clean[f["id"]] = str(v)[:2000]
    p["fields"] = clean
    p["lastUpdated"] = now()
    p["lastUpdatedBy"] = user["id"]
    _save_project(p)
    _log(project_id, "UPDATED", user["id"], "Draft saved")
    return "Project saved successfully."


def submit(user, project_id):
    p = project(project_id)
    if not can_edit(user, p):
        raise Denied("This project has already been submitted.")
    resubmission = p["approvalStatus"] == "REJECTED" or (p.get("submissionCount") or 0) > 0
    p["previousSubmittedFields"] = p.get("currentSubmittedFields")
    p["currentSubmittedFields"] = dict(p["fields"])
    p["approvalStatus"] = "SUBMITTED"
    p["submittedBy"] = user["id"]
    p["submittedAt"] = now()
    p["submissionCount"] = (p.get("submissionCount") or 0) + 1
    p["rejectionReason"] = None
    p["rejectedBy"] = None
    p["rejectedAt"] = None
    p["lastUpdated"] = p["submittedAt"]
    p["lastUpdatedBy"] = user["id"]
    _save_project(p)
    _log(project_id, "RESUBMITTED" if resubmission else "SUBMITTED", user["id"],
         "Submission #%d" % p["submissionCount"])
    return "Project submitted for Delivery Head review."


def approve(user, project_id):
    p = project(project_id)
    if user["role"] != "DELIVERY_HEAD":
        raise Denied("Only the Delivery Head can approve a project.")
    if p["approvalStatus"] != "SUBMITTED":
        raise Denied("Only a submitted project can be approved.")
    p["approvalStatus"] = "APPROVED"
    p["approvedBy"] = user["id"]
    p["approvedAt"] = now()
    p["lastUpdated"] = p["approvedAt"]
    p["lastUpdatedBy"] = user["id"]
    _save_project(p)
    _log(project_id, "APPROVED", user["id"])
    return "Project approved."


def reject(user, project_id, reason):
    p = project(project_id)
    if user["role"] != "DELIVERY_HEAD":
        raise Denied("Only the Delivery Head can reject a project.")
    if p["approvalStatus"] != "SUBMITTED":
        raise Denied("Only a submitted project can be rejected.")
    reason = (reason or "").strip()
    if not reason:
        raise Denied("Enter a rejection reason before rejecting the project.")
    p["approvalStatus"] = "REJECTED"
    p["rejectedBy"] = user["id"]
    p["rejectedAt"] = now()
    p["rejectionReason"] = reason
    p["lastUpdated"] = p["rejectedAt"]
    p["lastUpdatedBy"] = user["id"]
    _save_project(p)
    _log(project_id, "REJECTED", user["id"], reason)
    return "Project rejected and returned to the Delivery Manager."


def short_date(iso):
    if not iso:
        return "—"
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso
    return d.strftime("%d-%b-%Y %H:%M")
