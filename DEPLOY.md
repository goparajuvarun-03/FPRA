# Putting the demo online — GitHub + Streamlit Community Cloud

Streamlit Community Cloud runs **Python** apps only, so the Node build in this repo can't be hosted there. `streamlit_app.py` is a Streamlit port of the same application — same two roles, same workflow, the same 584 workbook-derived fields, all as text boxes, same JSON file storage, no database, no Excel upload. Deploy that and you get a public `https://<something>.streamlit.app` link you can send to anyone.

Both builds share one repo. Keep the Node version for delivery; use the Streamlit version for the demo link.

---

## 1. Check it runs locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py          # http://localhost:8501
python test_streamlit_app.py            # 37 checks, end to end
```

## 2. Push to GitHub

Create an empty repo on GitHub (public is simplest — Streamlit Cloud can read private repos too, it just asks for extra permissions), then:

```bash
cd project-delivery-management
git init
git add .
git commit -m "Project Delivery Management — delivery manager / delivery head workflow"
git branch -M main
git remote add origin https://github.com/<your-username>/project-delivery-management.git
git push -u origin main
```

The repo must contain `streamlit_app.py` and `requirements.txt` at its root — Streamlit Cloud looks for exactly that. `.gitignore` keeps `data/` out of version control; the app seeds those JSON files itself on first run.

## 3. Deploy

1. Go to **share.streamlit.io** and sign in with GitHub.
2. **Create app → Deploy a public app from GitHub**.
3. Repository `<your-username>/project-delivery-management`, branch `main`, main file path `streamlit_app.py`.
4. Optional: **Advanced settings → App URL** to choose the subdomain, and Python version 3.11 or later.
5. **Deploy**. First build takes a couple of minutes; after that your link is live.

Every `git push` to `main` redeploys automatically.

## 4. Share the link

Send `https://<your-app>.streamlit.app` with the demo credentials:

| Username | Password | Role |
|---|---|---|
| `manager1` | `manager123` | Delivery Manager (4 projects) |
| `manager2` | `manager123` | Delivery Manager (3 projects) |
| `head1` | `head123` | Delivery Head (all 10 projects) |

Suggested five-minute walkthrough:

1. Sign in as `manager1` → **My projects** — only their four projects, with approval status per project.
2. Open **P001** → the section picker walks through all ten template sections; every field is a text box. Change a value → **Save draft** → **Submit for review**. The fields lock.
3. Sign out, sign in as `head1` → **All projects** — all ten, with a Delivery Manager filter.
4. Open **P005** → *What changed since the previous submission* shows four fields with previous and new values. **Reject** with a reason.
5. Back as `manager2` → the rejection comment is on the project, the fields are editable again, correct and resubmit.
6. As `head1` → **Approve**, then **Audit history** for the full trail.

**Reset demo data** in the sidebar puts everything back to the starting state between demos.

---

## Things worth knowing before you demo

- **Anyone with the link can open the app.** Streamlit Community Cloud public apps have no access control of their own — the sign-in screen here is application-level only, and the demo passwords are in this repo. Don't put real project data in it. To gate the whole app, add a shared passphrase in **App settings → Secrets** and check it before the login screen renders.
- **Storage is ephemeral.** Community Cloud gives the container a temporary filesystem, so saved values survive while the app is up but reset when it restarts, sleeps, or redeploys. Fine for a demo; for anything durable, host on a machine with a persistent disk and point `PDM_DATA_DIR` at it.
- **One shared copy of the data.** Every visitor hits the same container, so two people demoing at once will see each other's edits. For side-by-side demos, deploy two apps from the same repo.
- **Apps sleep after about a week of inactivity** and wake on the next visit — the first load after that is slow. Open the link yourself an hour before a demo.
- **Free tier resources are modest.** The level-wise sections render 130 text boxes at a time, which is the heaviest screen. Rendering one section at a time keeps it responsive.

## If you'd rather demo the Node build

The Node application is the fuller UI (all sections on one page, sticky action bar, no rerun on every keystroke). It won't run on Streamlit Cloud, but it deploys as-is anywhere that runs Node — for example on Render: **New → Web Service**, connect the repo, build command `npm install` (there are no dependencies, so it's a no-op), start command `node seed.js && node server.js`, and it will bind to the port in `PORT` automatically. Railway, Fly.io and Azure App Service work the same way. Those hosts also give you a public HTTPS URL.
