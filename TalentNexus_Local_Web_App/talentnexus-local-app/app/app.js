const appState = { user: null, view: "home", profiles: [], selectedId: null, search: "", cases: [] };
const $ = (selector) => document.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}
function initials(name) { return String(name || "TN").split(/\s+/).slice(0, 2).map(x => x[0] || "").join("").toUpperCase(); }
function percent(done, total) { return total ? Math.round(done * 100 / total) : 0; }
function userRoleLabel() { return appState.user?.role === "people_partner" ? "People Partner" : "Manager · Team 1"; }
async function api(path, options = {}) {
  const response = await fetch(path, { credentials: "same-origin", ...options, headers: { ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }), ...(options.headers || {}) } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) { const error = new Error(data.error || `Request failed (${response.status})`); error.data = data; error.status = response.status; throw error; }
  return data;
}
function notify(message, isError = false) {
  const toast = $("#toast"); toast.textContent = message; toast.hidden = false; toast.classList.toggle("error", isError);
  clearTimeout(notify.timer); notify.timer = setTimeout(() => { toast.hidden = true; }, 3700);
}
function showLogin(error = "") {
  appState.user = null; $("#loginScreen").hidden = false; $("#appShell").hidden = true;
  $("#loginError").textContent = error; $("#loginError").hidden = !error;
}
function setShell() {
  $("#loginScreen").hidden = true; $("#appShell").hidden = false;
  $("#userName").textContent = appState.user.name; $("#userRole").textContent = userRoleLabel(); $("#userInitial").textContent = initials(appState.user.name);
  renderNav();
}
function navItems() {
  if (appState.user.role === "people_partner") return [{ id: "home", label: "Overview", icon: "◫" }, { id: "employees", label: "Employees", icon: "♙" }, { id: "cases", label: "Case study library", icon: "▤" }];
  return [{ id: "home", label: "Team dashboard", icon: "◫" }, { id: "employees", label: "My team", icon: "♙" }, { id: "cases", label: "Case references", icon: "▤" }];
}
function renderNav() {
  $("#mainNav").innerHTML = navItems().map(item => `<button class="nav-button ${appState.view === item.id ? "active" : ""}" data-view="${item.id}"><span class="nav-icon">${item.icon}</span>${item.label}</button>`).join("");
  document.querySelectorAll(".nav-button").forEach(button => button.addEventListener("click", () => navigate(button.dataset.view)));
}
async function navigate(view) {
  appState.view = view; renderNav();
  $("#viewLabel").textContent = navItems().find(item => item.id === view)?.label || "Overview";
  if (view === "home") return renderDashboard();
  if (view === "employees") return renderEmployees();
  if (view === "cases") return renderCases();
}
async function fetchProfiles() {
  const data = await api("/api/profiles"); appState.profiles = data.profiles;
  return appState.profiles;
}
function metricCard(label, value, note, icon) {
  return `<div class="metric-card"><div class="metric-label">${label}<span class="metric-icon">${icon}</span></div><div class="metric-value">${value}</div><div class="metric-note">${note}</div></div>`;
}
function profileRows(profiles) {
  return `<div class="employee-list">${profiles.map(profile => {
    const pct = percent(profile.training_completed, profile.training_total);
    return `<div class="employee-row" data-profile="${escapeHtml(profile.id)}" tabindex="0" role="button" aria-label="Open ${escapeHtml(profile.full_name)} profile">
      <div><div class="employee-name">${escapeHtml(profile.full_name)}</div><div class="employee-sub">${escapeHtml(profile.job_title)} · ${escapeHtml(profile.grade)}</div></div>
      <div class="cell hide-mobile">${escapeHtml(profile.team_name)}</div>
      <div class="cell hide-mobile">${escapeHtml(profile.tenure_years)} yrs</div>
      <div class="cell"><div class="progress-track"><span style="width:${pct}%"></span></div><div class="progress-label">${profile.training_completed}/${profile.training_total} learning</div></div>
      <div class="cell">›</div>
    </div>`;
  }).join("")}</div>`;
}
function wireProfileRows() {
  document.querySelectorAll("[data-profile]").forEach(row => {
    const open = () => openProfile(row.dataset.profile);
    row.addEventListener("click", open); row.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(); } });
  });
}
function dashboardContent(summary) {
  const profiles = summary.recent_profiles;
  const avg = summary.training_average;
  const pp = appState.user.role === "people_partner";
  const heading = pp ? "Good morning, Aarav" : "Good morning, Priya";
  const subtitle = pp ? "Your employee portfolio at a glance. Open a profile to review source-linked context." : "Your team at a glance. Prepare a 1:1 using approved, shareable context.";
  const summaryLabel = pp ? "Employees in portfolio" : "Employees on your team";
  return `<div class="page-head"><div><div class="eyebrow eyebrow-blue">${pp ? "PEOPLE PARTNER WORKSPACE" : "MANAGER WORKSPACE"}</div><h1>${heading}</h1><p>${subtitle}</p></div><button class="button-primary" id="browseProfiles">${pp ? "Open employee list" : "View my team"} &nbsp;→</button></div>
    <div class="metric-grid">${metricCard(summaryLabel, summary.profile_count, "Synthetic demo profiles", "♙")}${metricCard("Learning completion", `${avg}%`, "Across visible profiles", "✓")}${metricCard("Case studies", summary.case_count, "Available to this role", "▤")}${metricCard("AI recommendations", "Case-grounded", "Abstains without matching evidence", "✦")}</div>
    <div class="overview-grid grid"><section class="panel"><div class="panel-head"><div><h2>${pp ? "Employee portfolio" : "My team"}</h2><p>Open a profile to view evidence and prepare a conversation.</p></div><button class="tiny-link" id="allEmployees">View all →</button></div>${profileRows(profiles)}</section>
      <section class="panel"><div class="panel-head"><div><h2>How Talent Nexus supports you</h2><p>Role-scoped, advisory guidance</p></div></div><div class="activity-list">
      <div class="activity-item"><span class="activity-icon">✦</span><div><strong>Recommendations use uploaded case studies</strong><small>Only retrieved case-study excerpts can support an AI recommendation.</small></div></div>
      <div class="activity-item"><span class="activity-icon">⌕</span><div><strong>Sources and dates stay visible</strong><small>Profile facts show their source system and as-of date.</small></div></div>
      <div class="activity-item"><span class="activity-icon">◉</span><div><strong>Missing evidence means abstention</strong><small>No generalized recommendation is generated when cases do not match.</small></div></div>
    </div><div class="notice" style="margin-top:16px"><strong>Advisory only.</strong> Recommendations support a human conversation; they do not establish promotion eligibility or make employment decisions.</div></section></div>
    <div class="case-banner"><div><h2>Build recommendations from your case studies</h2><p>Upload approved case-study material. The app retrieves relevant excerpts and sends only those excerpts with role-visible synthetic facts to local Ollama.</p></div><button class="button-secondary" id="openCases">${pp ? "Manage case studies" : "View case references"} →</button></div>`;
}
async function renderDashboard() {
  const content = $("#content"); content.innerHTML = `<div class="loading">Loading role-scoped overview…</div>`;
  try {
    const [dash, cases] = await Promise.all([api("/api/dashboard"), api("/api/cases")]); appState.cases = cases.cases;
    content.innerHTML = dashboardContent({ ...dash, case_count: cases.cases.length });
    $("#browseProfiles").onclick = () => navigate("employees"); $("#allEmployees").onclick = () => navigate("employees"); $("#openCases").onclick = () => navigate("cases");
    wireProfileRows();
  } catch (error) { content.innerHTML = `<div class="notice">${escapeHtml(error.message)}</div>`; }
}
async function renderEmployees() {
  const content = $("#content"); content.innerHTML = `<div class="loading">Loading authorized profiles…</div>`;
  try {
    const profiles = await fetchProfiles();
    content.innerHTML = `<div class="page-head"><div><div class="eyebrow eyebrow-blue">${appState.user.role === "manager" ? "AUTHORIZED TEAM" : "AUTHORIZED PORTFOLIO"}</div><h1>${appState.user.role === "manager" ? "My team" : "Employees"}</h1><p>Only profiles visible to your current demo role are listed.</p></div><div class="search-box"><span>⌕</span><input id="profileSearch" type="search" placeholder="Search by name, title, or team" value="${escapeHtml(appState.search)}"></div></div><div id="employeeCards" class="profile-grid"></div>`;
    const search = $("#profileSearch");
    const draw = () => {
      appState.search = search.value;
      const q = search.value.toLowerCase();
      const filtered = profiles.filter(p => `${p.full_name} ${p.job_title} ${p.team_name} ${p.grade}`.toLowerCase().includes(q));
      $("#employeeCards").innerHTML = filtered.length ? filtered.map(p => {
        const pct = percent(p.training_completed, p.training_total);
        return `<article class="profile-card" data-profile="${escapeHtml(p.id)}" tabindex="0"><div class="profile-card-head"><span class="avatar">${initials(p.full_name)}</span><div><h3>${escapeHtml(p.full_name)}</h3><p>${escapeHtml(p.job_title)} · ${escapeHtml(p.grade)}</p></div></div><div class="profile-meta"><span>${escapeHtml(p.team_name)}</span><span><strong>${escapeHtml(p.tenure_years)}</strong> yrs tenure</span></div><div class="progress-track"><span style="width:${pct}%"></span></div><div class="progress-label"><span>Learning completed</span><span>${p.training_completed}/${p.training_total}</span></div></article>`;
      }).join("") : `<div class="empty-state"><strong>No matching profiles</strong>Try another name or team.</div>`;
      wireProfileRows();
    };
    search.addEventListener("input", draw); draw();
  } catch (error) { content.innerHTML = `<div class="notice">${escapeHtml(error.message)}</div>`; }
}
async function openProfile(id) {
  appState.selectedId = id; appState.view = "profile"; renderNav(); $("#viewLabel").textContent = "Employee profile";
  const content = $("#content"); content.innerHTML = `<div class="loading">Loading authorized profile…</div>`;
  try {
    const data = await api(`/api/profile?id=${encodeURIComponent(id)}`); renderProfile(data.profile);
  } catch (error) { content.innerHTML = `<div class="notice">${escapeHtml(error.message)}</div>`; }
}
function recordLabel(field) {
  return ({ profile: "Role and grade", performance_summary: "Performance summary", skills: "Skills", career_history: "Career history", allocation: "Current allocation", learning: "Learning", development_goal: "Development goal", certification: "Certification", project_outcome: "Project outcome", manager_feedback: "Manager feedback", reward: "Rewards", promotion_history: "Promotion history", private_checkin: "Private check-in", mentoring: "Mentoring", mobility_interest: "Mobility interest", recognition: "Recognition" })[field] || field.replaceAll("_", " ");
}
function valueText(value) { return Array.isArray(value) ? value.join(" · ") : String(value); }
function renderProfile(profile) {
  const pp = appState.user.role === "people_partner";
  const identity = appState.user.role === "manager" ? "Team member profile" : "Employee profile";
  const visible = profile.records || [];
  const group = visible.map(record => `<div class="record-item"><div><strong>${escapeHtml(recordLabel(record.field))}</strong><p>${escapeHtml(valueText(record.value))}</p></div><div class="source">${escapeHtml(record.source_system)}<br>As of ${escapeHtml(record.as_of)}</div></div>`).join("");
  $("#content").innerHTML = `<div class="page-head"><div><button class="tiny-link" id="backToList">← Back to ${pp ? "employees" : "my team"}</button><div class="eyebrow eyebrow-blue" style="margin-top:11px">${identity.toUpperCase()}</div></div><span class="status-chip green">Authorized view</span></div>
    <div class="profile-hero"><span class="avatar">${initials(profile.full_name)}</span><div><h2>${escapeHtml(profile.full_name)}</h2><p>${escapeHtml(profile.job_title)} · ${escapeHtml(profile.grade)} · ${escapeHtml(profile.department)}</p><span class="subtle">${escapeHtml(profile.team_name)} · ${escapeHtml(profile.tenure_years)} years at company</span></div><div class="right"><span class="subtle">PROFILE ID</span><div class="employee-name">${escapeHtml(profile.id)}</div></div></div>
    <div class="profile-details grid"><div class="detail-card"><small>Performance summary</small><strong>${escapeHtml(profile.performance_summary)}</strong></div><div class="detail-card"><small>Development goal</small><strong>${escapeHtml((profile.development_goals || []).join("; ") || "No approved goal recorded")}</strong></div><div class="detail-card"><small>Learning completion</small><strong>${profile.training_completed} of ${profile.training_total} items</strong><div class="progress-track" style="margin-top:10px"><span style="width:${percent(profile.training_completed, profile.training_total)}%"></span></div></div></div>
    <div class="records-layout"><section class="panel"><div class="panel-head"><div><h2>Employee 360 · evidence</h2><p>${visible.length} authorized records · source and as-of date shown for each</p></div></div><div class="record-grid">${group}</div></section>
      <aside class="recommend-panel"><h2>✦ Case-grounded recommendation</h2><p>Recommendations use only relevant uploaded case studies and the facts visible to your role. No case match means the app abstains.</p>
      <label class="small-label" for="recommendationQuery">What would you like to explore?</label><textarea id="recommendationQuery" class="text-input">Based only on the case studies, suggest a development conversation for this employee's stated goal.</textarea>
      <button id="generateRecommendation" class="button-primary" style="width:100%;margin-top:10px">Generate recommendation</button><div id="recommendationResult"></div>
      <div class="notice" style="margin-top:13px"><strong>Advisory only.</strong> This output is not a rating, promotion decision, or employment action.</div>
    </aside></div>`;
  $("#backToList").onclick = () => navigate("employees");
  $("#generateRecommendation").onclick = () => generateRecommendation(profile.id);
}
function refsHtml(refs) {
  if (!refs?.length) return `<p class="subtle">No case-study references were used.</p>`;
  return `<div class="reference-list">${refs.map(ref => `<div class="reference"><strong>${escapeHtml(ref.title)} · ${escapeHtml(ref.filename)}</strong><small>Retrieved match · ${Math.round(ref.score * 100)}% relevance</small><p>${escapeHtml(ref.excerpt)}</p></div>`).join("")}</div>`;
}
async function generateRecommendation(employeeId) {
  const button = $("#generateRecommendation"), result = $("#recommendationResult"), query = $("#recommendationQuery").value;
  button.disabled = true; button.textContent = "Finding case evidence…"; result.innerHTML = `<div class="loading">Searching the approved case-study library and calling local Ollama…</div>`;
  try {
    const data = await api("/api/recommendation", { method: "POST", body: JSON.stringify({ employee_id: employeeId, query }) });
    if (data.status === "abstained") {
      result.innerHTML = `<div class="result-card"><h3>Recommendation withheld</h3><p>${escapeHtml(data.reason || "The current case studies do not support a specific recommendation.")}</p>${data.caveats?.length ? `<p class="caveat">${data.caveats.map(escapeHtml).join("<br>")}</p>` : ""}${refsHtml(data.case_references)}</div>`;
    } else {
      result.innerHTML = `<div class="result-card"><h3>Recommendation · ${escapeHtml(data.model || "local model")}</h3><p>${escapeHtml(data.recommendation)}</p>${data.rationale ? `<p>${escapeHtml(data.rationale)}</p>` : ""}${data.caveats?.length ? `<p class="caveat">${data.caveats.map(escapeHtml).join("<br>")}</p>` : ""}${data.discussion_questions?.length ? `<p><strong>Conversation prompts</strong><br>${data.discussion_questions.map(escapeHtml).join("<br>")}</p>` : ""}<strong class="subtle">Retrieved case-study evidence</strong>${refsHtml(data.case_references)}</div>`;
    }
  } catch (error) {
    result.innerHTML = `<div class="result-card"><h3>Recommendation not generated</h3><p>${escapeHtml(error.message)}</p>${refsHtml(error.data?.case_references)}</div>`;
  } finally { button.disabled = false; button.textContent = "Generate recommendation"; }
}
async function renderCases() {
  const content = $("#content"); content.innerHTML = `<div class="loading">Loading case-study library…</div>`;
  try {
    const data = await api("/api/cases"); appState.cases = data.cases;
    const pp = appState.user.role === "people_partner";
    content.innerHTML = `<div class="page-head"><div><div class="eyebrow eyebrow-blue">GROUNDING SOURCES</div><h1>${pp ? "Case study library" : "Case references"}</h1><p>Recommendations must be grounded in these materials; the app abstains when evidence is absent or unrelated.</p></div>${pp ? `<span class="status-chip">People Partner access</span>` : `<span class="status-chip">Approved for manager view</span>`}</div>
      <div class="upload-grid grid"><section class="panel"><div class="panel-head"><div><h2>${pp ? "Add approved case studies" : "Available references"}</h2><p>${pp ? "Files stay on this computer and are processed locally." : "Only case studies approved for manager sharing appear here."}</p></div></div>
      ${pp ? `<form id="caseUpload" class="upload-box"><label class="small-label" for="caseTitle">Display title</label><input id="caseTitle" name="title" class="text-input" placeholder="e.g. Development path for a lateral move"><label class="small-label" for="caseFile">Case-study file</label><input id="caseFile" name="file" type="file" accept=".pdf,.docx,.txt,.md,.csv,.json,.html" required><label class="check-row"><input type="checkbox" name="manager_shareable" value="true"><span>Allow this case study to be used in manager recommendations. Leave unchecked unless approved for manager sharing.</span></label><button class="button-primary" type="submit">Upload to local library</button><div id="uploadError" class="error-message" hidden></div></form>` : `<div class="notice">Case studies are People Partner-only by default. A People Partner must mark a case as manager-shareable before it appears here.</div>`}
      </section><section class="panel"><div class="panel-head"><div><h2>Library contents</h2><p id="caseCount">${data.cases.length} case studies available</p></div></div><div id="caseRows">${caseRows(data.cases, pp)}</div></section></div>
      <div class="notice" style="margin-top:16px"><strong>Source constraint.</strong> The case-study files were not included with this build request. Until approved files are uploaded, AI recommendations abstain instead of using generalized knowledge. Use synthetic/approved case material only.</div>`;
    if (pp) $("#caseUpload").addEventListener("submit", uploadCaseStudy);
    wireDeleteCases();
  } catch (error) { content.innerHTML = `<div class="notice">${escapeHtml(error.message)}</div>`; }
}
function caseRows(cases, allowDelete) {
  if (!cases.length) return `<div class="empty-state"><strong>No case studies loaded</strong>Recommendations will abstain until relevant approved material is uploaded.</div>`;
  return cases.map(item => `<div class="case-row"><span class="case-file-icon">▤</span><div class="case-row-body"><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.filename)} · ${item.characters.toLocaleString()} characters · ${escapeHtml(item.uploaded_at)}${item.manager_shareable ? " · manager-shareable" : " · People Partner-only"}</small></div>${allowDelete ? `<button class="button-danger" data-delete-case="${escapeHtml(item.id)}">Remove</button>` : ""}</div>`).join("");
}
async function uploadCaseStudy(event) {
  event.preventDefault(); const form = event.currentTarget, errorEl = $("#uploadError"), button = form.querySelector("button[type=submit]");
  errorEl.hidden = true; button.disabled = true; button.textContent = "Extracting text…";
  const formData = new FormData(form); formData.set("manager_shareable", form.elements.manager_shareable.checked ? "true" : "false");
  try { await api("/api/cases/upload", { method: "POST", body: formData }); notify("Case study added to the local library."); renderCases(); }
  catch (error) { errorEl.textContent = error.message; errorEl.hidden = false; button.disabled = false; button.textContent = "Upload to local library"; }
}
function wireDeleteCases() {
  document.querySelectorAll("[data-delete-case]").forEach(button => button.addEventListener("click", async () => {
    if (!window.confirm("Remove this case study from the local library?")) return;
    try { await api("/api/cases/delete", { method: "POST", body: JSON.stringify({ id: button.dataset.deleteCase }) }); notify("Case study removed."); renderCases(); }
    catch (error) { notify(error.message, true); }
  }));
}
async function login(demoUser) {
  try { const data = await api("/api/login", { method: "POST", body: JSON.stringify({ demo_user: demoUser }) }); appState.user = data.user; appState.view = "home"; appState.search = ""; setShell(); await navigate("home"); }
  catch (error) { showLogin(error.message); }
}
async function logout() { await api("/api/logout", { method: "POST", body: "{}" }).catch(() => {}); appState.profiles = []; appState.selectedId = null; showLogin(); }

document.querySelectorAll("[data-login]").forEach(button => button.addEventListener("click", () => login(button.dataset.login)));
$("#logoutButton").addEventListener("click", logout);
api("/api/session").then(data => { if (data.user) { appState.user = data.user; setShell(); navigate("home"); } else showLogin(); }).catch(() => showLogin("Start the local server and refresh this page."));
