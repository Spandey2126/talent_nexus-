# TalentNexus Local Web App

A local, synthetic-data TalentNexus prototype based on the application context and the supplied People Partner and Manager portal HTMLs. The UI follows their navy/blue palette, card layout, role dashboards, employee profiles, worklists, and insight-focused flow.

## What is included

- People Partner and Manager demo views, with the Manager restricted to Team 1.
- 30 synthetic employee profiles and 16 named data domains.
- Server-side filtering of profile records before they reach the browser or local model. Pay, talent tags, private check-ins, promotion history, rewards, mentoring notes, and other People Partner-only fields are withheld from managers.
- Profile evidence with source system and as-of date.
- Local case-study library for PDF, DOCX, TXT, Markdown, CSV, JSON, and HTML files. The source documents remain on this computer; the app stores extracted text for retrieval.
- Case-study retrieval followed by optional local Ollama generation. The model receives only the relevant case excerpts and the active role's visible profile context.
- Abstention when no case studies are uploaded, no sufficiently relevant case is found, or the model says the evidence is insufficient. There is no generalized fallback recommendation.
- Manager access to a case study is opt-in at upload time and defaults to People Partner-only.
- Local references to the original context document and both supplied clickable HTML prototypes in `references/`.

## Prerequisites

- Python 3.10 or newer.
- Ollama for AI recommendations. The UI and synthetic profile views work without Ollama; recommendation requests will explain how to connect it.
- Optional for PDF uploads: the `pypdf` dependency installed below. DOCX extraction uses the Python standard library.

## Install and run

### Windows PowerShell

```powershell
cd talentnexus-local-app
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull llama3:latest
python server.py
```

### macOS / Linux

```bash
cd talentnexus-local-app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull llama3:latest
python server.py
```

Open **http://127.0.0.1:8000**. If Ollama is not already running, start it in another terminal with `ollama serve`. To use another local Ollama model or port, set `OLLAMA_MODEL` and `OLLAMA_URL` before starting the app.

There are no passwords in this prototype. Choose a seeded role on the welcome screen:

- **People Partner** — sees the full synthetic portfolio and can upload/remove case studies.
- **Manager** — sees only Team 1 and case studies explicitly marked manager-shareable.

## Add case studies

Sign in as People Partner, choose **Case study library**, select a text-based PDF, DOCX, TXT, MD, CSV, JSON, or HTML file, and upload it. Check the manager-shareable box only when the material is approved for that role. The app extracts document text locally and keeps it in `data/case_studies/`.

The uploaded case studies were not present in the supplied files at build time. Until relevant case-study material is uploaded, the recommendation endpoint abstains. Recommendations use local Ollama (`llama3:latest` by default) and the retrieved case excerpts; no case-study text or profile data is sent to a hosted AI service.

## Data and local files

- `data/synthetic_profiles.json` is generated from `data/generate_seed.py` and contains only fictional profiles.
- `data/case_studies/` is empty on first run. Uploaded extracted text is stored here as JSON. Remove this folder's contents to clear the local case library.
- `references/` contains the source context document and supplied prototype HTML files for traceability.

## Important scope

This is a local hackathon/demo build, not production software. The sign-in screen is a role selector, not identity verification. Do not load live employee data or unapproved case studies. The app does not determine promotion eligibility, make employment decisions, or trigger HR actions. Review the source references, field classifications, and manager-sharing permissions with the project owner before using real data or deploying it.

## Repository

This app was prepared for the TalentNexus project repository: https://github.com/Spandey2126/talent_nexus- (default branch `main`). This local folder has not been pushed to GitHub.
