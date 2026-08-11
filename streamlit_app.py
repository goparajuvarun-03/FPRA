"""Project Delivery Management — Streamlit build (for the public demo link).

Same two roles, same workflow, same 584 workbook-derived fields, all rendered as
plain text boxes. No database: everything is stored in JSON files under data/.
No Excel upload anywhere — the workbook was read once during development and its
fields live in field_config.py.
"""

import streamlit as st

import field_config as CFG
import store

st.set_page_config(page_title="Project Delivery Management", page_icon="◧", layout="wide")

store.ensure_data()

CSS = """
<style>
  .block-container { padding-top: 2.2rem; max-width: 100%; }
  [data-testid="stSidebar"] { background: #16273a; }
  [data-testid="stSidebar"] * { color: #cfdce8; }
  [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 { color: #ffffff; }
  .pdm-badge { display:inline-block; font-size:11px; letter-spacing:.08em; text-transform:uppercase;
      padding:3px 9px; border-radius:999px; border:1px solid; font-family:ui-monospace,monospace; }
  .DRAFT      { background:#eef1f4; color:#5b6a7a; border-color:#c6d0da; }
  .SUBMITTED  { background:#fdf3e2; color:#a86a12; border-color:#e8d3ad; }
  .APPROVED   { background:#e6f3ed; color:#1e6f52; border-color:#b9dccb; }
  .REJECTED   { background:#fbeceb; color:#a83232; border-color:#eec4c1; }
  .pdm-sheet { font-family:ui-monospace,monospace; font-size:11px; letter-spacing:.1em;
      text-transform:uppercase; color:#8797a8; }
  .pdm-colhead { font-family:ui-monospace,monospace; font-size:10.5px; letter-spacing:.05em;
      text-transform:uppercase; color:#8797a8; text-align:center; padding-bottom:2px; }
  .pdm-rowhead { font-size:13px; color:#16202b; padding-top:8px; }
  .pdm-meta { color:#5b6a7a; font-size:13px; }
  div[data-testid="stTextInput"] input { font-family:ui-monospace,monospace; font-size:12.5px; }
  div[data-testid="column"] { min-width: 0; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- helpers
def badge(status):
    label = "Pending review" if status == "SUBMITTED" else status.title()
    return '<span class="pdm-badge %s">%s</span>' % (status, label)


def ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def open_project(project_id):
    st.session_state.view = "project"
    st.session_state.project_id = project_id
    load_values(project_id)


def load_values(project_id):
    """Reset the working copy and drop stale widget state."""
    p = store.project(project_id)
    st.session_state["field_values"] = dict(p["fields"])
    for k in [k for k in st.session_state.keys() if k.startswith("f_")]:
        del st.session_state[k]


def sync(field_id):
    st.session_state["field_values"][field_id] = st.session_state["f_" + field_id]


def text_box(field_id, label, editable):
    """The only field renderer in the application: always a text box."""
    key = "f_" + field_id
    if key not in st.session_state:
        st.session_state[key] = st.session_state["field_values"].get(field_id, "")
    return st.text_input(
        label,
        key=key,
        disabled=not editable,
        on_change=sync if editable else None,
        args=(field_id,) if editable else None,
        label_visibility="collapsed" if label.startswith(" ") else "visible",
    )


# ---------------------------------------------------------------- login
def login_screen():
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("#### Fixed price · POC accrual")
        st.title("Project Delivery Management")
        st.write(
            "Delivery Managers record baseline, effort, resource and financial information each month. "
            "The Delivery Head reviews what changed and approves or returns it."
        )
        st.caption("%d fields · %d sections · JSON file storage · no database"
                   % (CFG.FIELD_COUNT, len(CFG.SECTIONS)))
    with right:
        st.subheader("Sign in")
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary", width="stretch")
        if submitted:
            user = store.authenticate(username, password)
            if user:
                st.session_state.user = user
                st.session_state.view = "dashboard"
                st.rerun()
            else:
                st.error("That username and password combination is not recognised.")
        st.caption("Demo accounts")
        st.code("manager1 / manager123   Delivery Manager\n"
                "manager2 / manager123   Delivery Manager\n"
                "manager3 / manager123   Delivery Manager\n"
                "head1    / head123      Delivery Head", language=None)


# ---------------------------------------------------------------- sidebar
def sidebar(user):
    with st.sidebar:
        st.markdown("### Project Delivery Management")
        st.caption("Delivery")
        is_head = user["role"] == "DELIVERY_HEAD"
        options = ["All projects" if is_head else "My projects"] + (["Audit history"] if is_head else [])
        current = "Audit history" if st.session_state.view == "audit" else options[0]
        choice = st.radio("Navigation", options, index=options.index(current), label_visibility="collapsed")
        if choice == "Audit history" and st.session_state.view != "audit":
            st.session_state.view = "audit"
            st.rerun()
        if choice != "Audit history" and st.session_state.view not in ("dashboard", "project"):
            st.session_state.view = "dashboard"
            st.rerun()

        st.divider()
        st.write("**%s**" % user["name"])
        st.caption("DELIVERY HEAD" if is_head else "DELIVERY MANAGER · %s" % user["id"])
        if st.button("Sign out", width="stretch"):
            st.session_state.clear()
            st.rerun()
        with st.expander("Demo data"):
            st.caption("Resets all projects and the audit log to the starting state.")
            if st.button("Reset demo data", width="stretch"):
                store.reset_data()
                st.session_state.view = "dashboard"
                st.session_state.pop("project_id", None)
                st.rerun()


# ---------------------------------------------------------------- dashboard
def dashboard(user):
    is_head = user["role"] == "DELIVERY_HEAD"
    st.title("All projects" if is_head else "My projects")
    st.caption("Every project, every Delivery Manager" if is_head
               else "Projects assigned to %s" % user["name"])

    rows = store.projects_for(user)
    counts = {"DRAFT": 0, "SUBMITTED": 0, "APPROVED": 0, "REJECTED": 0}
    for p in rows:
        counts[p["approvalStatus"]] += 1
    cols = st.columns(5)
    for col, (n, k) in zip(cols, [(len(rows), "Total projects"), (counts["DRAFT"], "Draft"),
                                  (counts["SUBMITTED"], "Pending review"),
                                  (counts["APPROVED"], "Approved"), (counts["REJECTED"], "Rejected")]):
        col.metric(k, n)

    f1, f2, f3, f4 = st.columns([2, 1, 1, 1.2])
    query = f1.text_input("Search", placeholder="Search project, ID or client").strip().lower()
    approval = f2.selectbox("Approval status", ["All", "DRAFT", "SUBMITTED", "APPROVED", "REJECTED"])
    pstatus = f3.selectbox("Project status", ["All", "Active", "Planning", "On Hold"])
    manager = "All"
    if is_head:
        names = {u["id"]: u["name"] for u in store.users() if u["role"] == "DELIVERY_MANAGER"}
        manager = f4.selectbox("Delivery Manager", ["All"] + list(names.values()))
        rev = {v: k for k, v in names.items()}

    filtered = []
    for p in rows:
        if approval != "All" and p["approvalStatus"] != approval:
            continue
        if pstatus != "All" and p["projectStatus"] != pstatus:
            continue
        if is_head and manager != "All" and p["deliveryManagerId"] != rev[manager]:
            continue
        if query:
            hay = " ".join([p["id"], p["name"], p["client"],
                            store.user_name(p["deliveryManagerId"])]).lower()
            if query not in hay:
                continue
        filtered.append(p)

    st.caption("%d of %d projects" % (len(filtered), len(rows)))
    widths = [1, 3, 2, 2, 1.4, 1.6, 1.2] if is_head else [1, 3, 2, 1.4, 1.6, 1.2]
    header = ["Project ID", "Project", "Delivery Manager", "Client", "Status", "Approval", ""] if is_head \
        else ["Project ID", "Project", "Client", "Status", "Approval", ""]
    head_cols = st.columns(widths)
    for col, label in zip(head_cols, header):
        col.markdown('<div class="pdm-sheet">%s</div>' % label, unsafe_allow_html=True)
    st.divider()

    if not filtered:
        st.info("No projects match these filters. Clear the search or pick a different status.")
        return

    for p in filtered:
        c = st.columns(widths)
        c[0].code(p["id"], language=None)
        c[1].write("**%s**" % p["name"])
        i = 2
        if is_head:
            c[2].write(store.user_name(p["deliveryManagerId"]))
            i = 3
        c[i].write(p["client"])
        c[i + 1].write(p["projectStatus"])
        c[i + 2].markdown(badge(p["approvalStatus"]), unsafe_allow_html=True)
        label = ("Review" if p["approvalStatus"] == "SUBMITTED" else "View") if is_head \
            else ("Edit" if store.can_edit(user, p) else "View")
        if c[i + 3].button(label, key="open_" + p["id"], width="stretch"):
            open_project(p["id"])
            st.rerun()


# ---------------------------------------------------------------- project screen
def project_screen(user):
    p = store.project(st.session_state.project_id)
    if p is None or not store.can_open(user, p):
        st.error("This project is assigned to another Delivery Manager.")
        return
    editable = store.can_edit(user, p)
    is_head = user["role"] == "DELIVERY_HEAD"

    if st.button("← Back to projects"):
        st.session_state.view = "dashboard"
        st.rerun()

    head, right = st.columns([4, 1])
    head.title(p["name"])
    right.markdown(badge(p["approvalStatus"]), unsafe_allow_html=True)
    head.markdown(
        '<div class="pdm-meta">Project ID: <b>%s</b> · Client: <b>%s</b> · Delivery Manager: <b>%s</b> · '
        'Project status: <b>%s</b> · Submissions: <b>%d</b> · Last updated: <b>%s</b></div>'
        % (p["id"], p["client"], store.user_name(p["deliveryManagerId"]), p["projectStatus"],
           p.get("submissionCount") or 0, store.short_date(p["lastUpdated"])),
        unsafe_allow_html=True)
    st.write("")

    if p["approvalStatus"] == "REJECTED":
        st.error("**Returned by the Delivery Head** — %s  \n_%s_"
                 % (p["rejectionReason"], store.short_date(p["rejectedAt"])))
    elif p["approvalStatus"] == "SUBMITTED" and not is_head:
        st.info("Submitted on %s. The fields are locked while the Delivery Head reviews this submission."
                % store.short_date(p["submittedAt"]))
    elif p["approvalStatus"] == "APPROVED":
        st.success("Approved by the Delivery Head on %s. This project is read-only."
                   % store.short_date(p["approvedAt"]))
    elif is_head and p["approvalStatus"] == "DRAFT":
        st.info("This project is still a draft with the Delivery Manager. There is nothing to approve yet.")

    diffs = store.changes(p)
    if diffs:
        with st.expander("What changed since the previous submission — %d field%s"
                         % (len(diffs), "" if len(diffs) == 1 else "s"), expanded=is_head):
            st.dataframe(
                [{"Field": d["label"], "Sheet": d["sheet"],
                  "Previous value": d["previous"] or "—", "New value": d["new"] or "—"} for d in diffs],
                width="stretch", hide_index=True)

    # ---- fields ----
    st.divider()
    st.subheader("Edit project" if editable else "Project information")
    st.caption("All %d fields from the delivery template. Every field is a text box. "
               "Pick a section to work on — your entries are held until you save."
               % CFG.FIELD_COUNT)

    labels = ["%s · %s" % (s["sheet"], s["title"].replace("Section I: ", "").replace("Section II: ", ""))
              for s in CFG.SECTIONS]
    picked = st.selectbox("Section", range(len(CFG.SECTIONS)), format_func=lambda i: labels[i],
                          key="section_idx")
    section = CFG.SECTIONS[picked]

    st.markdown('<div class="pdm-sheet">%s</div>' % section["sheet"], unsafe_allow_html=True)
    st.markdown("**%s**" % section["title"])
    if section.get("note"):
        st.caption(section["note"])

    if section["layout"] == "stack":
        cols = st.columns(3)
        for n, f in enumerate(section["fields"]):
            with cols[n % 3]:
                text_box("%s__%s" % (section["id"], f["id"]), f["label"], editable)
    else:
        widths = [3.2] + [1] * len(CFG.COLUMNS)
        head_cols = st.columns(widths, gap="small")
        head_cols[0].write("")
        for col, c in zip(head_cols[1:], CFG.COLUMNS):
            col.markdown('<div class="pdm-colhead">%s</div>' % c["label"], unsafe_allow_html=True)
        for row in section["rows"]:
            line = st.columns(widths, gap="small")
            line[0].markdown('<div class="pdm-rowhead">%s</div>' % row["label"], unsafe_allow_html=True)
            for col, c in zip(line[1:], CFG.COLUMNS):
                with col:
                    text_box("%s__%s__%s" % (section["id"], row["id"], c["key"]),
                             " %s — %s" % (row["label"], c["label"]), editable)

    # ---- actions ----
    st.divider()
    if editable:
        a, b, _ = st.columns([1, 1.4, 4])
        if a.button("Save draft", width="stretch"):
            st.toast(store.save_draft(user, p["id"], st.session_state["field_values"]), icon="✅")
            st.rerun()
        with b.popover("Submit for review", width="stretch"):
            st.write("Submit this project for Delivery Head review?")
            st.caption("Your latest values are saved first. Once submitted, the fields are locked "
                       "until the Delivery Head approves or returns the project.")
            if st.button("Submit", type="primary"):
                store.save_draft(user, p["id"], st.session_state["field_values"])
                st.toast(store.submit(user, p["id"]), icon="✅")
                load_values(p["id"])
                st.rerun()
    elif is_head and p["approvalStatus"] == "SUBMITTED":
        a, b, _ = st.columns([1, 1, 4])
        with a.popover("Approve", width="stretch"):
            st.write("Approve this project?")
            st.caption("The project becomes read-only for the Delivery Manager and is recorded in the audit history.")
            if st.button("Approve", type="primary"):
                st.toast(store.approve(user, p["id"]), icon="✅")
                st.rerun()
        with b.popover("Reject", width="stretch"):
            st.write("Reject this project")
            reason = st.text_area("Rejection reason",
                                  placeholder="Tell the Delivery Manager what needs to change.")
            if st.button("Reject"):
                try:
                    st.toast(store.reject(user, p["id"], reason), icon="↩️")
                    st.rerun()
                except store.Denied as err:
                    st.error(str(err))

    # ---- history ----
    entries = store.audit_entries(p["id"])
    if entries:
        with st.expander("Project history — %d entries" % len(entries)):
            st.dataframe(
                [{"Action": e["action"], "By": store.user_name(e["performedBy"]),
                  "When": store.short_date(e["timestamp"]), "Detail": e["detail"] or "—"} for e in entries],
                width="stretch", hide_index=True)


# ---------------------------------------------------------------- audit
def audit_screen(user):
    if user["role"] != "DELIVERY_HEAD":
        st.error("Only the Delivery Head can view the full audit history.")
        return
    st.title("Audit history")
    entries = store.audit_entries()
    st.caption("%d entries" % len(entries))
    st.dataframe(
        [{"Project": e["projectId"], "Action": e["action"], "By": store.user_name(e["performedBy"]),
          "When": store.short_date(e["timestamp"]), "Detail": e["detail"] or "—"} for e in entries],
        width="stretch", hide_index=True)


# ---------------------------------------------------------------- router
ss("view", "dashboard")
ss("field_values", {})
user = st.session_state.get("user")

if not user:
    login_screen()
else:
    sidebar(user)
    if st.session_state.view == "project" and st.session_state.get("project_id"):
        project_screen(user)
    elif st.session_state.view == "audit":
        audit_screen(user)
    else:
        dashboard(user)
