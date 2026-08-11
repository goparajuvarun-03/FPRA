"""Workflow test for the Streamlit build. Run: python test_streamlit_app.py

Drives the real app through Streamlit's AppTest harness: login, edit, save,
submit, reject, correct, resubmit, change comparison, approve.
"""

import sys

from streamlit.testing.v1 import AppTest

import field_config as CFG
import seed_data
import store

PASS, FAIL = [], []


def check(label, ok, extra=""):
    (PASS if ok else FAIL).append(label)
    print(("  PASS  " if ok else "  FAIL  ") + label + (("  → " + str(extra)) if not ok and extra else ""))


def app():
    return AppTest.from_file("streamlit_app.py", default_timeout=300).run()


def login(at, username, password):
    at.text_input[0].set_value(username)
    at.text_input[1].set_value(password)
    at.button[0].click().run()
    return at


def button(at, label):
    return next(b for b in at.button if b.label == label)


def main():
    seed_data.build(store.DATA_DIR)
    print("\n1. Login and role scoping")
    at = app()
    login(at, "manager1", "nope")
    check("Wrong password is rejected", len(at.error) == 1 and "not recognised" in at.error[0].value)

    at = login(app(), "manager1", "manager123")
    check("Delivery Manager signs in", at.title[0].value == "My projects", at.exception)
    check("Manager One sees only their 4 projects", at.metric[0].value == "4")

    head = login(app(), "head1", "head123")
    check("Delivery Head signs in", head.title[0].value == "All projects", head.exception)
    check("Delivery Head sees all 10 projects", head.metric[0].value == "10")

    print("\n2. Fields on the edit screen")
    at.button(key="open_P001").click().run()
    check("Project opens without error", not at.exception, at.exception)
    check("Header shows the project", at.title[0].value == "Atlas Core Migration")
    check("First section renders its 7 text boxes", len(at.text_input) == 7, len(at.text_input))
    at.selectbox(key="section_idx").set_value(1).run()
    check("Monthwise section renders 3 rows x 13 columns of text boxes",
          len(at.text_input) == 39, len(at.text_input))
    at.selectbox(key="section_idx").set_value(7).run()
    check("Level-wise section renders 10 rows x 13 columns of text boxes",
          len(at.text_input) == 130, len(at.text_input))
    total = 0
    for i in range(len(CFG.SECTIONS)):
        at.selectbox(key="section_idx").set_value(i).run()
        total += len(at.text_input)
    check("All %d configured fields render as text boxes across the sections" % CFG.FIELD_COUNT,
          total == CFG.FIELD_COUNT, total)

    print("\n3. Save draft")
    at.selectbox(key="section_idx").set_value(2).run()  # Efforts
    at.text_input(key="f_efforts__effortsActual__m2026_07").set_value("950").run()
    button(at, "Save draft").click().run()
    check("Save draft persists to JSON",
          store.project("P001")["fields"]["efforts__effortsActual__m2026_07"] == "950")
    check("Status is still DRAFT", store.project("P001")["approvalStatus"] == "DRAFT")

    print("\n4. Submit for review")
    button(at, "Submit").click().run()
    check("Status becomes SUBMITTED", store.project("P001")["approvalStatus"] == "SUBMITTED")
    check("Fields are now read-only for the manager", all(t.disabled for t in at.text_input),
          [t.key for t in at.text_input if not t.disabled][:3])
    check("No Save draft button on a submitted project",
          not any(b.label == "Save draft" for b in at.button))

    print("\n5. Delivery Head rejects")
    dh = login(app(), "head1", "head123")
    dh.button(key="open_P001").click().run()
    check("Delivery Head sees read-only fields", all(t.disabled for t in dh.text_input))
    check("Approve and Reject are offered",
          any(b.label == "Approve" for b in dh.button) and any(b.label == "Reject" for b in dh.button))
    button(dh, "Reject").click().run()
    check("Rejecting with an empty reason is refused",
          len(dh.error) == 1 and "rejection reason" in dh.error[0].value.lower())
    dh.text_area[0].set_value("Efforts Actual for Jul-2026 needs to match the timesheet extract.").run()
    button(dh, "Reject").click().run()
    p = store.project("P001")
    check("Status becomes REJECTED", p["approvalStatus"] == "REJECTED")
    check("Rejection reason is stored", "timesheet extract" in (p["rejectionReason"] or ""))

    print("\n6. Manager corrects and resubmits")
    at = login(app(), "manager1", "manager123")
    at.button(key="open_P001").click().run()
    check("Manager sees the rejection comment",
          any("Returned by the Delivery Head" in e.value for e in at.error))
    check("Rejected project is editable again", not any(t.disabled for t in at.text_input))
    at.selectbox(key="section_idx").set_value(2).run()
    at.text_input(key="f_efforts__effortsActual__m2026_07").set_value("1100").run()
    button(at, "Save draft").click().run()
    button(at, "Submit").click().run()
    check("Resubmission lands as SUBMITTED", store.project("P001")["approvalStatus"] == "SUBMITTED")
    diffs = store.changes(store.project("P001"))
    check("Change comparison shows exactly the corrected field", len(diffs) == 1, [d["label"] for d in diffs])
    check("Change shows 950 → 1100",
          diffs and diffs[0]["previous"] == "950" and diffs[0]["new"] == "1100")

    print("\n7. Delivery Head approves")
    dh = login(app(), "head1", "head123")
    dh.button(key="open_P001").click().run()
    check("Change table is rendered for the reviewer", len(dh.dataframe) >= 1)
    button(dh, "Approve").click().run()
    p = store.project("P001")
    check("Status becomes APPROVED", p["approvalStatus"] == "APPROVED")
    check("approvedBy is stored", p["approvedBy"] == "DH001")
    at = login(app(), "manager1", "manager123")
    at.button(key="open_P001").click().run()
    check("Approved project is read-only for the manager", all(t.disabled for t in at.text_input))

    print("\n8. Audit history")
    actions = [e["action"] for e in store.audit_entries("P001")]
    for a in ["CREATED", "UPDATED", "SUBMITTED", "REJECTED", "RESUBMITTED", "APPROVED"]:
        check("Audit log records " + a, a in actions, actions)
    dh = login(app(), "head1", "head123")
    dh.radio[0].set_value("Audit history").run()
    check("Delivery Head can open the audit screen", dh.title[0].value == "Audit history", dh.exception)

    seed_data.build(store.DATA_DIR)
    print("\n%s — %d passed, %d failed.\n"
          % ("ALL CHECKS PASSED" if not FAIL else "%d CHECK(S) FAILED" % len(FAIL), len(PASS), len(FAIL)))
    sys.exit(0 if not FAIL else 1)


if __name__ == "__main__":
    main()
