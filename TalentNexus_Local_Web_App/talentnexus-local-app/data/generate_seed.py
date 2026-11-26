"""Regenerate the deterministic, fully synthetic TalentNexus demo data."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
names = [
    ("Maya Thomas", "Senior Analyst"), ("Kabir Nair", "Product Analyst"), ("Isha Menon", "Consultant"),
    ("Arjun Mehta", "Data Engineer"), ("Tara Iyer", "Business Analyst"), ("Rohan Das", "QA Engineer"),
    ("Neha Kapoor", "Project Lead"), ("Dev Malhotra", "Software Engineer"), ("Anaya Bose", "People Analyst"),
    ("Vihaan Shah", "Operations Specialist"), ("Zoya Khan", "Senior Consultant"), ("Kunal Rao", "UX Designer"),
    ("Aditi Sinha", "Program Manager"), ("Reyansh Patel", "Data Scientist"), ("Meera Joshi", "Business Partner"),
    ("Ishaan Kulkarni", "Cloud Engineer"), ("Sara Thomas", "Associate Consultant"), ("Aarav Gupta", "Product Owner"),
    ("Diya Nair", "Learning Specialist"), ("Nikhil Verma", "Developer"), ("Myra Desai", "Delivery Lead"),
    ("Advik Shah", "Finance Analyst"), ("Anika Rao", "Security Analyst"), ("Ritvik Sen", "Service Manager"),
    ("Kiara Menon", "Research Analyst"), ("Samar Bhat", "Platform Engineer"), ("Riya Chawla", "HR Analyst"),
    ("Yash Arora", "Technical Lead"), ("Sana Mirza", "Client Partner"), ("Neil Fernandes", "Operations Lead"),
]
skills_pool = ["Stakeholder communication", "Data analysis", "Project delivery", "Coaching", "Process design", "Product thinking", "Quality engineering", "Cloud platforms", "Facilitation", "Risk analysis", "Customer discovery", "Technical writing"]
goals_pool = ["Lead a cross-functional initiative", "Build advanced data storytelling skills", "Practice mentoring peers", "Develop product strategy experience", "Strengthen cloud architecture skills", "Facilitate customer workshops", "Improve quality engineering practices", "Expand people leadership experience"]
ratings = ["Strong delivery across committed outcomes", "Consistent results with room to broaden scope", "High quality work and dependable collaboration", "Growing ownership of complex assignments", "Positive stakeholder feedback on recent work"]
sources = ["CompanyDeavor", "CompanyFulcrum", "CompanyFusion", "Learning Portal", "Rewards Portal", "Promotion Portal", "People Partner Portal"]
datasets = [
    {"name": "Employee profile", "source_system": "CompanyDeavor", "visibility": "manager-shareable"},
    {"name": "Performance summary", "source_system": "CompanyFusion", "visibility": "manager-shareable"},
    {"name": "Skills", "source_system": "CompanyFulcrum", "visibility": "manager-shareable"},
    {"name": "Career history", "source_system": "CompanyDeavor", "visibility": "manager-shareable"},
    {"name": "Allocation", "source_system": "CompanyFulcrum", "visibility": "manager-shareable"},
    {"name": "Learning", "source_system": "Learning Portal", "visibility": "manager-shareable"},
    {"name": "Rewards", "source_system": "Rewards Portal", "visibility": "people-partner-only"},
    {"name": "Promotion", "source_system": "Promotion Portal", "visibility": "people-partner-only"},
    {"name": "Check-in commitments", "source_system": "People Partner Portal", "visibility": "people-partner-only"},
    {"name": "Development goals", "source_system": "CompanyFulcrum", "visibility": "manager-shareable"},
    {"name": "Certifications", "source_system": "Learning Portal", "visibility": "manager-shareable"},
    {"name": "Mentoring", "source_system": "People Partner Portal", "visibility": "people-partner-only"},
    {"name": "Project outcomes", "source_system": "CompanyFusion", "visibility": "manager-shareable"},
    {"name": "Manager feedback", "source_system": "CompanyFusion", "visibility": "manager-shareable"},
    {"name": "Mobility interest", "source_system": "CompanyDeavor", "visibility": "people-partner-only"},
    {"name": "Recognition", "source_system": "Rewards Portal", "visibility": "people-partner-only"},
]
profiles = []
for i, (name, title) in enumerate(names, 1):
    team_num = 1 + ((i - 1) // 10)
    team_id = f"team-{team_num}"
    grade_num = 5 + (i % 4)
    skill_set = [skills_pool[(i * 2 + j * 3) % len(skills_pool)] for j in range(3)]
    goal = goals_pool[i % len(goals_pool)]
    completed = (i * 7) % 11
    total = 10
    records = []
    def add(field, value, dataset, visible_to, as_of="2026-10-31"):
        d = next(x for x in datasets if x["name"] == dataset)
        records.append({"field": field, "value": value, "dataset": dataset, "source_system": d["source_system"], "as_of": as_of, "visible_to": visible_to})
    add("profile", f"{title} · Grade {grade_num}", "Employee profile", ["people_partner", "manager"])
    add("performance_summary", ratings[i % len(ratings)], "Performance summary", ["people_partner", "manager"])
    add("skills", skill_set, "Skills", ["people_partner", "manager"])
    add("career_history", f"{i % 5 + 2} years in role family · {i % 4 + 1} role changes", "Career history", ["people_partner", "manager"])
    add("allocation", ["Platform Modernization", "Customer Experience", "Data Enablement", "Process Excellence"][i % 4], "Allocation", ["people_partner", "manager"])
    add("learning", f"{completed} of {total} assigned learning items completed", "Learning", ["people_partner", "manager"])
    add("reward", ["Peer recognition", "Team contribution award", "No recent award record"][i % 3], "Rewards", ["people_partner"])
    add("promotion_history", f"Last role change recorded {i % 4 + 1} years ago; eligibility requires HR review", "Promotion", ["people_partner"])
    add("private_checkin", f"Private check-in note {i:02d}: not approved for manager sharing", "Check-in commitments", ["people_partner"])
    add("development_goal", goal, "Development goals", ["people_partner", "manager"])
    add("certification", ["Cloud Foundations", "Agile Delivery", "Data Fundamentals", "No current certification record"][i % 4], "Certifications", ["people_partner", "manager"])
    add("mentoring", ["Mentors one peer", "Participates in a mentoring circle", "No current mentoring record"][i % 3], "Mentoring", ["people_partner"])
    add("project_outcome", ["Delivered a workflow improvement", "Supported a cross-team release", "Improved reporting quality", "Contributed to service reliability"][i % 4], "Project outcomes", ["people_partner", "manager"])
    add("manager_feedback", ["Communicates progress clearly", "Collaborates well across functions", "Growing confidence in ambiguous work"][i % 3], "Manager feedback", ["people_partner", "manager"])
    add("mobility_interest", ["Open to adjacent role exploration", "No mobility preference recorded", "Interested in broader project exposure"][i % 3], "Mobility interest", ["people_partner"])
    add("recognition", ["Recognized for collaboration", "Recognized for customer focus", "No recent recognition record"][i % 3], "Recognition", ["people_partner"])
    profiles.append({
        "id": f"emp-{i:03d}", "full_name": name, "job_title": title, "grade": f"G{grade_num}",
        "department": ["People & Culture", "Technology", "Client Delivery"][i % 3],
        "team_id": team_id, "team_name": f"Team {team_num}",
        "manager_name": "Priya Shah" if team_num == 1 else f"Manager {team_num}",
        "tenure_years": round(1.2 + ((i * 17) % 75) / 10, 1),
        "training_completed": completed, "training_total": total, "records": records,
        "pay_band": f"Private band {grade_num}", "talent_tag": "Confidential talent label", "private_notes": "Synthetic PP-only note; never share with manager agent."
    })

(ROOT / "data" / "synthetic_profiles.json").write_text(json.dumps({"datasets": datasets, "profiles": profiles}, indent=2, ensure_ascii=False), encoding="utf-8")
print("Wrote synthetic profile fixture")
