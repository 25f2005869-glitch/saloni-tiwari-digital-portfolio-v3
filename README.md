# Saloni Tiwari — Complete Digital Identity & Portfolio (v3)

This version upgrades the supplied static portfolio into a **Flask + SQLite application** with a public portfolio and a server-side authenticated Admin Panel.

## Run locally on Windows

1. Extract the ZIP to a normal folder (for example `Documents\Saloni_Tiwari_Complete_Portfolio_v3`).
2. Open that folder in File Explorer.
3. Right-click `Start-Portfolio.ps1` → **Run with PowerShell**. If Windows blocks scripts, open PowerShell in the folder and run:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\run_local.ps1
   ```

4. The first run installs the packages and asks you to create an Admin password. Keep it private.
5. Open the public site at `http://127.0.0.1:5000`.
6. Open `http://127.0.0.1:5000/login` to sign in. Username: `saloni`; password: the one you created.

The local app binds to `127.0.0.1`, so it is not exposed to other computers on your network.

## Admin features

- Project Manager: add, edit, delete, category, description, tools, GitHub/demo links, thumbnail upload.
- Certificate Manager: add/edit/delete credentials from CBSE, Bihar Board, Magadh University, IIT Madras, AWS, Coursera, Kaggle, other universities and platforms. Upload PDF/image files.
- Media Manager: photos, images, GIFs, videos, PDF, PPT/PPTX and PBIX files.
- Education, Skills, Achievements and Learning Journey managers.
- JSON export/import backup. Import adds records and does not overwrite existing records.
- Public/private visibility toggle on each record.

## Content carried forward

- All 28 project records from the supplied portfolio ZIP.
- All 15 original numbered project thumbnails, the Finance & FinTech thumbnail and E-Commerce preview.
- Existing professional photographs.
- Existing Kaggle, Coursera, AWS Academy and IIT Madras certificate files.
- E-Commerce Sales Dashboard PBIX and PDF.
- Education records for IIT Madras and Magadh University.

Certificate counts follow the user's corrected totals: Kaggle 9; Coursera 4 certificates covering 10 completed courses; AWS 1 training badge; IIT Madras 8. Some certificate scan files were not in the source ZIP. Those credential records are listed without fabricated scans, and Admin can attach the originals later. CBSE Class 10, Bihar Board Class 12 and Magadh University certificate categories are ready for the actual documents; no missing certificate has been invented.

## Important hosting difference

**GitHub Pages cannot run Flask, SQLite or server-side login.** Do not replace the currently published static site with this backend project on GitHub Pages and expect Admin authentication to work. Keep GitHub as source-code storage if you like, then deploy this Flask application to a Python host that supports persistent storage (for example Render with a persistent disk). Configure these environment variables on the host:

- `ADMIN_USERNAME=saloni`
- `ADMIN_PASSWORD` = a strong unique password (never commit it)
- `SECRET_KEY` = a long random secret
- `COOKIE_SECURE=1` when HTTPS is enabled
- `PORT` is normally supplied by the host

Configure persistent storage for both `portfolio.db` and `static/uploads`. Back up the database and uploads regularly. Use HTTPS. Do not upload private marksheets, IDs, date of birth, home address or confidential records to a public portfolio. Only mark documents public when you intentionally want visitors to view them.

## Local checks

- Public route: `/`
- Login: `/login`
- Private dashboard: `/admin` (redirects to login when not authenticated)
- Health check: `/health`
