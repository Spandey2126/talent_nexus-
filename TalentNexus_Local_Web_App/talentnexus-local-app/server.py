#!/usr/bin/env python3
"""Local-only TalentNexus demo server. Uses synthetic profiles and local Ollama."""

from __future__ import annotations

import hashlib
import html
import http.cookies
import http.server
import json
import os
import re
import secrets
import socketserver
import threading
import time
import urllib.error
import urllib.request
import zipfile
from email.parser import BytesParser
from email.policy import default
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "synthetic_profiles.json"
CASE_DIR = ROOT / "data" / "case_studies"
STATIC_DIR = ROOT / "app"
PORT = int(os.environ.get("PORT", "8000"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:latest")
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_CASE_TEXT = 300_000

SESSIONS: dict[str, dict] = {}
SESSION_LOCK = threading.Lock()


def load_data() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def load_cases() -> list[dict]:
    CASE_DIR.mkdir(parents=True, exist_ok=True)
    found = []
    for path in sorted(CASE_DIR.glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            if item.get("text", "").strip():
                found.append(item)
        except (OSError, json.JSONDecodeError):
            continue
    return found


def session_for(handler: "Handler") -> dict | None:
    cookie = http.cookies.SimpleCookie()
    try:
        cookie.load(handler.headers.get("Cookie", ""))
        token = cookie.get("tn_session").value if cookie.get("tn_session") else ""
    except (http.cookies.CookieError, AttributeError):
        token = ""
    with SESSION_LOCK:
        return SESSIONS.get(token)


def user_for_demo(demo_user: str) -> dict | None:
    if demo_user == "people-partner":
        return {"id": "pp-demo", "name": "Aarav Rao", "role": "people_partner", "team_id": None}
    if demo_user == "manager":
        return {"id": "manager-demo", "name": "Priya Shah", "role": "manager", "team_id": "team-1"}
    return None


def profile_for(employee_id: str) -> dict | None:
    return next((p for p in load_data()["profiles"] if p["id"] == employee_id), None)


def allowed_profile(user: dict, employee_id: str) -> dict | None:
    profile = profile_for(employee_id)
    if not profile:
        return None
    if user["role"] == "manager" and profile["team_id"] != user["team_id"]:
        return None
    return profile


def visible_records(profile: dict, role: str) -> list[dict]:
    if role == "people_partner":
        return profile["records"]
    return [r for r in profile["records"] if "manager" in r.get("visible_to", [])]


def safe_profile(profile: dict, role: str) -> dict:
    result = {k: v for k, v in profile.items() if k not in ("records", "private_notes", "pay_band", "talent_tag")}
    result["records"] = visible_records(profile, role)
    result["skills"] = [r["value"] for r in result["records"] if r["field"] == "skills"]
    result["development_goals"] = [r["value"] for r in result["records"] if r["field"] == "development_goal"]
    result["performance_summary"] = next((r["value"] for r in result["records"] if r["field"] == "performance_summary"), "Not available")
    return result


def visible_cases(user: dict) -> list[dict]:
    cases = load_cases()
    if user["role"] == "people_partner":
        return cases
    return [case for case in cases if case.get("manager_shareable") is True]


STOP_WORDS = set("a an the and or but of for to from in on with by is are was were be been being this that these those it its as at about my our their your employee profile talent recommendation recommend case study studies please should could would do does has have based only relevant evidence review development conversation career skill skills ready readiness promotion promote manager people partner team member what who why how which tell me give an insight".split())
SYNONYMS = {
    "promotion": {"advancement", "promoted", "progression", "grade", "level"},
    "advancement": {"promotion", "promoted", "progression"},
    "leadership": {"leader", "lead", "management", "managerial"},
    "learning": {"training", "course", "development", "skill"},
    "skills": {"skill", "competency", "competencies", "capability"},
    "performance": {"rating", "review", "delivery", "outcome"},
    "readiness": {"ready", "eligibility", "eligible", "promotion"},
}


def tokens(text: str) -> set[str]:
    base = {word.lower() for word in re.findall(r"[a-zA-Z0-9]+", text) if len(word) > 2}
    base -= STOP_WORDS
    expanded = set(base)
    for word in base:
        expanded.update(SYNONYMS.get(word, set()))
    return expanded


def retrieve_cases(user: dict, profile: dict, query: str, limit: int = 3) -> list[dict]:
    corpus = visible_cases(user)
    query_terms = tokens(query)
    profile_terms = tokens(" ".join(str(r["value"]) for r in visible_records(profile, user["role"])))
    terms = query_terms | profile_terms
    scored = []
    for case in corpus:
        body = case["text"]
        case_terms = tokens((case.get("title") or "") + " " + body)
        overlap = terms & case_terms
        if not overlap:
            continue
        query_overlap = query_terms & case_terms
        # Give the user's question more weight; profile context is a secondary cue.
        score = (2.0 * len(query_overlap) + 0.35 * len(profile_terms & case_terms)) / max(1, len(query_terms) + 0.35 * len(profile_terms))
        if score >= 0.035:
            ranked = sorted(overlap, key=lambda x: (x not in query_overlap, -len(x)))
            excerpt = case.get("text", "")
            if len(excerpt) > 1100:
                pos = max((excerpt.lower().find(term) for term in ranked[:5]), default=0)
                start = max(0, pos - 220)
                excerpt = ("…" if start else "") + excerpt[start : start + 1100] + ("…" if start + 1100 < len(case.get("text", "")) else "")
            scored.append({"id": case["id"], "title": case["title"], "filename": case["filename"], "score": round(score, 3), "excerpt": excerpt})
    return sorted(scored, key=lambda c: c["score"], reverse=True)[:limit]


def parse_docx(raw: bytes) -> str:
    with zipfile.ZipFile(__import__("io").BytesIO(raw)) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    lines = []
    for para in root.findall(".//w:p", ns):
        line = "".join(node.text or "" for node in para.findall(".//w:t", ns)).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def parse_upload(filename: str, raw: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".json", ".html"}:
        text = raw.decode("utf-8-sig", errors="replace")
        if suffix == ".html":
            class TextOnly(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.bits = []
                def handle_data(self, data):
                    if data.strip():
                        self.bits.append(data.strip())
            parser = TextOnly()
            parser.feed(text)
            text = "\n".join(parser.bits)
        return text
    if suffix == ".docx":
        return parse_docx(raw)
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError("PDF import needs pypdf. Install requirements.txt and restart the app.") from exc
        import io
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages)
    raise ValueError("Supported formats: PDF, DOCX, TXT, MD, CSV, JSON, HTML.")


def ask_ollama(user: dict, profile: dict, query: str, cases: list[dict]) -> dict:
    role = "People Partner" if user["role"] == "people_partner" else "Manager"
    evidence = [{"case_id": c["id"], "title": c["title"], "excerpt": c["excerpt"]} for c in cases]
    evidence_fields = {"profile", "performance_summary", "skills", "career_history", "allocation", "learning", "development_goal", "certification", "project_outcome", "manager_feedback"}
    visible_data = {
        "employee": profile["full_name"],
        "title": profile["job_title"],
        "grade": profile["grade"],
        "skills": profile["skills"],
        "development_goals": profile["development_goals"],
        "performance_summary": profile["performance_summary"],
        "supporting_profile_facts": [r for r in profile["records"] if r["field"] in evidence_fields],
    }
    system = (
        "You are TalentNexus, an advisory talent conversation assistant. Use ONLY the supplied case-study excerpts and employee facts. "
        "Do not use general knowledge or invent evidence. Do not determine promotion eligibility or make an employment decision. "
        "If the case studies do not directly support a useful recommendation, set abstain=true. "
        "Do not infer aspirations, protected traits, or missing facts. Return JSON only with keys: abstain (boolean), recommendation (string), "
        "rationale (string), caveats (array of strings), discussion_questions (array of strings). Do not add citations; the application attaches verified case references."
    )
    prompt = json.dumps({"role": role, "request": query, "employee_context": visible_data, "case_studies": evidence}, ensure_ascii=False)
    payload = json.dumps({"model": OLLAMA_MODEL, "system": system, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0.1}}).encode()
    request = urllib.request.Request(OLLAMA_URL.rstrip("/") + "/api/generate", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            generated = json.loads(response.read().decode("utf-8"))
        result = json.loads(generated.get("response", "{}"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Local Ollama is not responding at {OLLAMA_URL} with model {OLLAMA_MODEL}. Start Ollama and pull the model, then retry.") from exc
    if not isinstance(result, dict) or not isinstance(result.get("abstain"), bool):
        raise RuntimeError("The model returned an invalid response. Try again or use a smaller local model.")
    if result.get("abstain"):
        result["recommendation"] = "No recommendation is supported by the currently matched case studies."
    if not isinstance(result.get("recommendation"), str):
        raise RuntimeError("The model response did not include a valid recommendation.")
    result["rationale"] = str(result.get("rationale", ""))[:2500]
    result["caveats"] = [str(x)[:400] for x in result.get("caveats", []) if isinstance(x, (str, int, float))][:6]
    result["discussion_questions"] = [str(x)[:400] for x in result.get("discussion_questions", []) if isinstance(x, (str, int, float))][:6]
    result["model"] = OLLAMA_MODEL
    return result


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "TalentNexusLocal/1.0"

    def log_message(self, fmt, *args):
        # Avoid recording queries or profile data in terminal logs.
        print(f"[{self.log_date_time_string()}] {self.command} {self.path.split('?')[0]}")

    def send_json(self, status: int, obj: dict, headers: dict | None = None):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        size = int(self.headers.get("Content-Length", "0"))
        if size > MAX_UPLOAD_BYTES:
            raise ValueError("Request is too large.")
        raw = self.rfile.read(size)
        return json.loads(raw or b"{}")

    def require_user(self) -> dict | None:
        user = session_for(self)
        if not user:
            self.send_json(401, {"error": "Sign in to the local demo first."})
            return None
        return user

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/session":
            user = session_for(self)
            self.send_json(200, {"user": user, "ollama_model": OLLAMA_MODEL, "ollama_url": OLLAMA_URL})
            return
        if parsed.path == "/api/health":
            self.send_json(200, {"status": "ok", "profiles": len(load_data()["profiles"]), "ollama_model": OLLAMA_MODEL})
            return
        if parsed.path == "/api/login-options":
            self.send_json(200, {"users": [{"key": "people-partner", "label": "People Partner", "name": "Aarav Rao"}, {"key": "manager", "label": "Manager · Team 1", "name": "Priya Shah"}]})
            return
        if parsed.path == "/" or parsed.path.startswith("/static/"):
            rel = "index.html" if parsed.path == "/" else parsed.path[len("/static/"):]
            target = (STATIC_DIR / rel).resolve()
            try:
                target.relative_to(STATIC_DIR.resolve())
            except ValueError:
                self.send_error(404)
                return
            if not target.is_file():
                self.send_error(404)
                return
            raw = target.read_bytes()
            types = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml"}
            self.send_response(200)
            self.send_header("Content-Type", types.get(target.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)
            return
        user = self.require_user()
        if not user:
            return
        if parsed.path == "/api/profiles":
            data = load_data()["profiles"]
            if user["role"] == "manager":
                data = [p for p in data if p["team_id"] == user["team_id"]]
            records = [safe_profile(p, user["role"]) for p in data]
            self.send_json(200, {"profiles": records})
            return
        if parsed.path == "/api/profile":
            employee_id = parse_qs(parsed.query).get("id", [""])[0]
            profile = allowed_profile(user, employee_id)
            if not profile:
                self.send_json(404, {"error": "Employee not found."})
                return
            self.send_json(200, {"profile": safe_profile(profile, user["role"])})
            return
        if parsed.path == "/api/cases":
            cases = visible_cases(user)
            self.send_json(200, {"cases": [{"id": c["id"], "title": c["title"], "filename": c["filename"], "uploaded_at": c["uploaded_at"], "manager_shareable": c.get("manager_shareable", False), "characters": len(c["text"])} for c in cases]})
            return
        if parsed.path == "/api/dashboard":
            profiles = load_data()["profiles"]
            if user["role"] == "manager":
                profiles = [p for p in profiles if p["team_id"] == user["team_id"]]
            completed = sum(1 for p in profiles if p["training_completed"])
            average = round(sum((p["training_completed"] * 100 / p["training_total"]) if p["training_total"] else 0 for p in profiles) / max(1, len(profiles)))
            self.send_json(200, {"profile_count": len(profiles), "training_completed": completed, "training_total": len(profiles), "training_average": average, "case_count": len(visible_cases(user)), "recent_profiles": [safe_profile(p, user["role"]) for p in profiles[:5]]})
            return
        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/login":
                body = self.read_json()
                user = user_for_demo(body.get("demo_user", ""))
                if not user:
                    self.send_json(400, {"error": "Choose one of the seeded demo roles."})
                    return
                token = secrets.token_urlsafe(30)
                with SESSION_LOCK:
                    SESSIONS[token] = user
                cookie = f"tn_session={token}; HttpOnly; SameSite=Strict; Path=/"
                self.send_json(200, {"user": user}, {"Set-Cookie": cookie})
                return
            if parsed.path == "/api/logout":
                cookie = http.cookies.SimpleCookie()
                cookie.load(self.headers.get("Cookie", ""))
                token = cookie.get("tn_session").value if cookie.get("tn_session") else ""
                with SESSION_LOCK:
                    SESSIONS.pop(token, None)
                self.send_json(200, {"ok": True}, {"Set-Cookie": "tn_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"})
                return
            user = self.require_user()
            if not user:
                return
            if parsed.path == "/api/recommendation":
                body = self.read_json()
                employee_id = str(body.get("employee_id", ""))
                query = str(body.get("query", ""))[:600]
                if len(query.strip()) < 4:
                    self.send_json(400, {"error": "Enter a short question or recommendation focus."})
                    return
                profile = allowed_profile(user, employee_id)
                if not profile:
                    self.send_json(404, {"error": "Employee not found."})
                    return
                cases = retrieve_cases(user, profile, query)
                if not visible_cases(user):
                    self.send_json(200, {"status": "abstained", "reason": "No case studies are available to this role. Upload case studies and mark them manager-shareable when appropriate.", "case_references": []})
                    return
                if not cases:
                    self.send_json(200, {"status": "abstained", "reason": "No sufficiently relevant case-study evidence was found. The app will not generate a generalized recommendation.", "case_references": []})
                    return
                try:
                    result = ask_ollama(user, safe_profile(profile, user["role"]), query, cases)
                except RuntimeError as exc:
                    self.send_json(503, {"error": str(exc), "case_references": cases})
                    return
                if result.get("abstain"):
                    self.send_json(200, {"status": "abstained", "reason": result.get("rationale") or result.get("recommendation"), "caveats": result.get("caveats", []), "case_references": cases, "model": result.get("model")})
                    return
                self.send_json(200, {"status": "grounded", "recommendation": result["recommendation"], "rationale": result.get("rationale", ""), "caveats": result.get("caveats", []), "discussion_questions": result.get("discussion_questions", []), "case_references": cases, "model": result.get("model")})
                return
            if parsed.path == "/api/cases/upload":
                if user["role"] != "people_partner":
                    self.send_json(403, {"error": "Only the People Partner demo role can add case studies."})
                    return
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > MAX_UPLOAD_BYTES:
                    self.send_json(413, {"error": "Upload must be between 1 byte and 20 MB."})
                    return
                raw_request = self.rfile.read(size)
                content_type = self.headers.get("Content-Type", "")
                message = BytesParser(policy=default).parsebytes((f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + raw_request))
                file_part = next((part for part in message.iter_parts() if part.get_filename()), None)
                if not file_part:
                    self.send_json(400, {"error": "Choose a case-study file."})
                    return
                filename = Path(file_part.get_filename()).name
                file_bytes = file_part.get_payload(decode=True) or b""
                text = parse_upload(filename, file_bytes).strip()
                if len(text) < 80:
                    self.send_json(400, {"error": "The file has too little extractable text. Use a text-based PDF/DOCX or TXT/MD/CSV/JSON/HTML."})
                    return
                if len(text) > MAX_CASE_TEXT:
                    text = text[:MAX_CASE_TEXT]
                fields = {part.get_param("name", header="content-disposition"): part.get_payload(decode=True).decode("utf-8", "replace") for part in message.iter_parts() if not part.get_filename()}
                manager_shareable = fields.get("manager_shareable", "false").lower() == "true"
                title = html.unescape(fields.get("title", "").strip()) or Path(filename).stem.replace("_", " ").replace("-", " ")
                digest = hashlib.sha256(file_bytes).hexdigest()[:16]
                record = {"id": "case-" + digest, "title": title[:120], "filename": filename[:180], "uploaded_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "manager_shareable": manager_shareable, "text": text, "sha256": hashlib.sha256(file_bytes).hexdigest()}
                CASE_DIR.mkdir(parents=True, exist_ok=True)
                (CASE_DIR / (record["id"] + ".json")).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                self.send_json(201, {"case": {k: record[k] for k in ("id", "title", "filename", "uploaded_at", "manager_shareable")}})
                return
            if parsed.path == "/api/cases/delete":
                if user["role"] != "people_partner":
                    self.send_json(403, {"error": "Only the People Partner demo role can remove case studies."})
                    return
                body = self.read_json()
                case_id = str(body.get("id", ""))
                if not re.fullmatch(r"case-[a-f0-9]{16}", case_id):
                    self.send_json(400, {"error": "Invalid case-study id."})
                    return
                target = CASE_DIR / (case_id + ".json")
                if target.exists():
                    target.unlink()
                self.send_json(200, {"ok": True})
                return
            self.send_error(404)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": str(exc) or "Invalid request."})
        except Exception:
            self.send_json(500, {"error": "The local app could not process this request."})


def main():
    CASE_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingServer(("127.0.0.1", PORT), Handler)
    print(f"TalentNexus local demo running at http://127.0.0.1:{PORT}")
    print(f"AI provider: Ollama at {OLLAMA_URL} · model {OLLAMA_MODEL}")
    print("Synthetic profiles only. This is a local demo, not production authentication.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping TalentNexus local demo…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
