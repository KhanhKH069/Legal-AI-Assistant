"""
Generate 100 realistic Vietnamese employee profiles for Paraline HR system.
Outputs:
  - data/employees_data.json  (rich profiles with skills, contracts, org chart)
  - data/hr_mock_data.csv     (extended to 100 rows for analytics)
  - data/appraisal_data.json  (performance appraisal mock data)
"""

import csv
import json
import os
import random
from datetime import date, timedelta

random.seed(42)

# ── Lookup tables ────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Nguyen",
    "Tran",
    "Le",
    "Phan",
    "Hoang",
    "Vu",
    "Do",
    "Ngo",
    "Bui",
    "Dinh",
    "Dao",
    "Duong",
    "Dang",
    "Mai",
    "Ly",
    "Ho",
    "Truong",
    "Lam",
    "Vo",
    "Pham",
]
MIDDLE_FEMALE = ["Thi", "Ngoc", "My", "Bich", "Lan", "Hoa", "Thu", "Huong"]
MIDDLE_MALE = ["Van", "Duc", "Quoc", "Minh", "Huu", "Cong", "Xuan", "Trong"]
GIVEN_NAMES_FEMALE = [
    "An",
    "Bich",
    "Chi",
    "Dung",
    "Em",
    "Giang",
    "Ha",
    "Hoa",
    "Lan",
    "Linh",
    "Mai",
    "Ngoc",
    "Nhi",
    "Oanh",
    "Phuong",
    "Quynh",
    "Suong",
    "Thao",
    "Uyen",
    "Van",
    "Yen",
    "Anh",
    "Chau",
    "Dao",
    "Hien",
    "Hong",
    "Huong",
    "Khanh",
    "Loan",
    "Ly",
    "My",
    "Nhung",
    "Tam",
    "Thuy",
    "Trang",
    "Truc",
    "Xuan",
]
GIVEN_NAMES_MALE = [
    "An",
    "Bao",
    "Cuong",
    "Dung",
    "Em",
    "Giang",
    "Hung",
    "Kien",
    "Long",
    "Minh",
    "Nam",
    "Phuc",
    "Quang",
    "Son",
    "Thanh",
    "Tuan",
    "Vinh",
    "Xuan",
    "Yen",
    "Hao",
    "Khoa",
    "Lam",
    "Nghia",
    "Phat",
    "Quan",
    "Sang",
    "Tai",
    "Uy",
    "Viet",
    "Khang",
    "Hieu",
    "Dat",
    "Bao",
    "Duc",
    "Huy",
    "Tri",
    "Thi",
]

DEPARTMENTS = {
    "Engineering": 25,
    "HR": 8,
    "Sales": 18,
    "Marketing": 10,
    "Finance": 8,
    "Product": 8,
    "QA": 7,
    "DevOps": 6,
    "Customer Success": 6,
    "Legal": 4,
}

POSITIONS = {
    "Engineering": [
        "Backend Developer",
        "Frontend Developer",
        "Full-stack Developer",
        "AI Engineer",
        "Engineering Manager",
        "Tech Lead",
        "Software Architect",
    ],
    "HR": [
        "HR Specialist",
        "HR Manager",
        "Recruiter",
        "HR Business Partner",
        "L&D Specialist",
    ],
    "Sales": [
        "Sales Executive",
        "Sales Manager",
        "Account Manager",
        "Business Development",
        "Sales Lead",
    ],
    "Marketing": [
        "Marketing Manager",
        "Content Creator",
        "SEO Specialist",
        "Digital Marketer",
        "Brand Manager",
    ],
    "Finance": [
        "Accountant",
        "Finance Manager",
        "Financial Analyst",
        "Payroll Specialist",
    ],
    "Product": ["Product Manager", "Product Owner", "UX Designer", "UX Researcher"],
    "QA": ["QA Engineer", "QA Lead", "Test Automation Engineer"],
    "DevOps": ["DevOps Engineer", "Cloud Engineer", "SRE", "DevOps Lead"],
    "Customer Success": ["CS Specialist", "CS Manager", "Technical Support"],
    "Legal": ["Legal Counsel", "Compliance Officer", "Legal Specialist"],
}

SKILLS_MAP = {
    "Engineering": [
        "Python",
        "Java",
        "TypeScript",
        "React",
        "Node.js",
        "FastAPI",
        "Docker",
        "Kubernetes",
        "PostgreSQL",
        "Redis",
        "Git",
        "AWS",
        "Microservices",
        "REST API",
        "GraphQL",
        "TDD",
        "CI/CD",
        "LangChain",
        "PyTorch",
    ],
    "HR": [
        "Talent Acquisition",
        "HRIS",
        "Labor Law Vietnam",
        "Performance Management",
        "Employee Relations",
        "Compensation & Benefits",
        "Training & Development",
        "SHRM",
        "Onboarding",
        "Payroll Processing",
    ],
    "Sales": [
        "CRM",
        "Salesforce",
        "Cold Calling",
        "B2B Sales",
        "Negotiation",
        "Pipeline Management",
        "Account Management",
        "HubSpot",
        "Closing",
        "Market Research",
    ],
    "Marketing": [
        "SEO",
        "Google Analytics",
        "Content Marketing",
        "Social Media",
        "Email Marketing",
        "Adobe Creative",
        "Copywriting",
        "PPC",
        "Canva",
        "Brand Strategy",
    ],
    "Finance": [
        "Excel",
        "SAP",
        "QuickBooks",
        "IFRS",
        "Financial Modeling",
        "Tax Law Vietnam",
        "Budgeting",
        "Cost Accounting",
        "Power BI",
    ],
    "Product": [
        "Figma",
        "Jira",
        "Agile/Scrum",
        "User Research",
        "Product Roadmap",
        "A/B Testing",
        "Prototyping",
        "Market Analysis",
        "OKRs",
    ],
    "QA": [
        "Selenium",
        "Cypress",
        "Postman",
        "JMeter",
        "TestRail",
        "Bug Tracking",
        "Manual Testing",
        "API Testing",
        "Performance Testing",
    ],
    "DevOps": [
        "Docker",
        "Kubernetes",
        "Terraform",
        "Ansible",
        "Jenkins",
        "GitLab CI",
        "AWS",
        "GCP",
        "Linux",
        "Prometheus",
        "Grafana",
        "Bash",
    ],
    "Customer Success": [
        "Zendesk",
        "Intercom",
        "Customer Onboarding",
        "NPS",
        "CRM",
        "SLA Management",
        "Communication",
        "Product Knowledge",
    ],
    "Legal": [
        "Contract Drafting",
        "Compliance",
        "Corporate Law",
        "IP Law",
        "Labor Law Vietnam",
        "Due Diligence",
        "Regulatory Affairs",
    ],
}

LEVELS = {
    "Junior": {
        "exp_min": 0,
        "exp_max": 2,
        "salary_min": 12_000_000,
        "salary_max": 22_000_000,
    },
    "Mid": {
        "exp_min": 2,
        "exp_max": 5,
        "salary_min": 22_000_000,
        "salary_max": 45_000_000,
    },
    "Senior": {
        "exp_min": 5,
        "exp_max": 10,
        "salary_min": 45_000_000,
        "salary_max": 80_000_000,
    },
    "Lead": {
        "exp_min": 8,
        "exp_max": 15,
        "salary_min": 70_000_000,
        "salary_max": 120_000_000,
    },
    "Manager": {
        "exp_min": 6,
        "exp_max": 20,
        "salary_min": 80_000_000,
        "salary_max": 160_000_000,
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────


def rand_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def gen_name(gender: str) -> str:
    last = random.choice(FIRST_NAMES)
    middle = random.choice(MIDDLE_FEMALE if gender == "F" else MIDDLE_MALE)
    given = random.choice(GIVEN_NAMES_FEMALE if gender == "F" else GIVEN_NAMES_MALE)
    return f"{last} {middle} {given}"


def gen_skills(dept: str, n: int = None) -> list[str]:
    pool = SKILLS_MAP.get(dept, ["Communication", "Microsoft Office"])
    common = ["Communication", "Problem Solving", "Teamwork", "Time Management"]
    all_skills = pool + common
    k = n or random.randint(4, 8)
    return random.sample(all_skills, min(k, len(all_skills)))


def pick_level(position: str) -> str:
    pos_lower = position.lower()
    if "manager" in pos_lower or "director" in pos_lower or "head" in pos_lower:
        return "Manager"
    if "lead" in pos_lower or "architect" in pos_lower or "senior" in pos_lower:
        return random.choice(["Lead", "Senior"])
    if "junior" in pos_lower:
        return "Junior"
    return random.choice(["Junior", "Mid", "Mid", "Senior"])


def gen_salary(level: str) -> int:
    lvl = LEVELS[level]
    return random.randint(lvl["salary_min"], lvl["salary_max"])


def gen_contract_dates(hire_date: date) -> dict:
    """Generate contract start/end; ~20% have contracts expiring within 60 days."""
    start = hire_date
    if random.random() < 0.20:
        end = date.today() + timedelta(days=random.randint(5, 55))
    else:
        years = random.choice([1, 2, 3])
        end = hire_date + timedelta(days=365 * years)
        while end < date.today():
            end += timedelta(days=365)
    return {"start": str(start), "end": str(end)}


def gen_phone() -> str:
    return f"09{random.randint(10_000_000, 99_999_999)}"


def gen_email(name: str, emp_id: str) -> str:
    parts = name.lower().split()
    slug = f"{parts[-1]}.{parts[0]}{emp_id[-3:]}"
    return f"{slug}@paraline.vn"


# ── Existing 15 employees (preserve exact IDs & names) ───────────────────────

EXISTING = [
    (
        "EMP001",
        "Nguyen Van A",
        "Engineering",
        "Backend Developer",
        2500,
        "2023-01-15",
        4.5,
        "Active",
        15,
        "M",
    ),
    (
        "EMP002",
        "Tran Thi B",
        "HR",
        "HR Specialist",
        1500,
        "2022-05-10",
        4.0,
        "Active",
        5,
        "F",
    ),
    (
        "EMP003",
        "Le Thi C",
        "Engineering",
        "Frontend Developer",
        2200,
        "2024-02-01",
        3.8,
        "Active",
        12,
        "F",
    ),
    (
        "EMP004",
        "Phan Van D",
        "Sales",
        "Sales Executive",
        1200,
        "2023-11-20",
        4.2,
        "Active",
        8,
        "M",
    ),
    (
        "EMP005",
        "Hoang Thi E",
        "Engineering",
        "QA Engineer",
        1800,
        "2021-08-05",
        4.8,
        "Active",
        18,
        "F",
    ),
    (
        "EMP006",
        "Vu Van F",
        "Marketing",
        "Marketing Manager",
        3000,
        "2020-03-12",
        4.6,
        "Active",
        20,
        "M",
    ),
    (
        "EMP007",
        "Do Thi G",
        "HR",
        "HR Manager",
        3500,
        "2019-11-25",
        4.3,
        "Active",
        22,
        "F",
    ),
    (
        "EMP008",
        "Ngo Van H",
        "Engineering",
        "Engineering Manager",
        4500,
        "2018-06-10",
        4.9,
        "Active",
        25,
        "M",
    ),
    (
        "EMP009",
        "Bui Thi I",
        "Sales",
        "Sales Manager",
        3200,
        "2021-01-20",
        4.1,
        "Active",
        14,
        "F",
    ),
    (
        "EMP010",
        "Dinh Van K",
        "Marketing",
        "Content Creator",
        1000,
        "2024-01-05",
        3.9,
        "Active",
        6,
        "M",
    ),
    (
        "EMP011",
        "Tran Van L",
        "Engineering",
        "DevOps Engineer",
        2800,
        "2022-09-15",
        4.4,
        "Resigned",
        0,
        "M",
    ),
    (
        "EMP012",
        "Le Thi M",
        "Sales",
        "Sales Executive",
        1300,
        "2023-04-10",
        3.5,
        "Resigned",
        0,
        "F",
    ),
    (
        "EMP013",
        "Nguyen Van N",
        "Marketing",
        "SEO Specialist",
        1400,
        "2023-07-22",
        4.0,
        "Active",
        9,
        "M",
    ),
    (
        "EMP014",
        "Hoang Van P",
        "Engineering",
        "AI Engineer",
        3000,
        "2024-03-01",
        4.7,
        "Active",
        10,
        "M",
    ),
    (
        "EMP015",
        "Phan Thi Q",
        "HR",
        "Recruiter",
        1600,
        "2023-10-05",
        4.2,
        "Active",
        7,
        "F",
    ),
]

# Manager map: dept → EMP_ID of manager
DEPT_MANAGER = {
    "Engineering": "EMP008",
    "HR": "EMP007",
    "Sales": "EMP009",
    "Marketing": "EMP006",
    "Finance": None,  # will be assigned
    "Product": None,
    "QA": None,
    "DevOps": None,
    "Customer Success": None,
    "Legal": None,
}

# ── Main generation ───────────────────────────────────────────────────────────


def build_employees() -> tuple[list[dict], list[dict]]:
    employees_json: list[dict] = []
    csv_rows: list[dict] = []

    # Salary USD → VND rough conversion factor already used in CSV (salary column is in USD $00s)
    # Keep CSV compatible (salary in hundreds USD, e.g. 2500 = $2500)

    # --- Process existing 15 first ---
    for idx, row in enumerate(EXISTING):
        (
            emp_id,
            name,
            dept,
            pos,
            sal_csv,
            hire_str,
            perf,
            status,
            leave_bal,
            gender,
        ) = row
        hire = date.fromisoformat(hire_str)
        level = pick_level(pos)
        sal_vnd = gen_salary(level)
        contract = gen_contract_dates(hire)
        skills = gen_skills(dept, random.randint(5, 9))
        emp = {
            "employee_id": emp_id,
            "name": name,
            "gender": gender,
            "department": dept,
            "position": pos,
            "level": level,
            "email": gen_email(name, emp_id),
            "phone": gen_phone(),
            "hire_date": hire_str,
            "status": status,
            "manager_id": DEPT_MANAGER.get(dept)
            if emp_id not in DEPT_MANAGER.values()
            else None,
            "salary_vnd": sal_vnd,
            "leave_balance": leave_bal,
            "performance_rating": perf,
            "skills": skills,
            "contract": contract,
            "address": f"Quận {random.randint(1, 12)}, TP.HCM",
            "emergency_contact": {
                "name": gen_name("F"),
                "phone": gen_phone(),
                "relation": "Spouse",
            },
            "education": random.choice(["Đại học", "Thạc sĩ", "Cao đẳng"]),
        }
        employees_json.append(emp)
        csv_rows.append(
            {
                "employee_id": emp_id,
                "name": name,
                "department": dept,
                "position": pos,
                "salary": sal_csv,
                "hire_date": hire_str,
                "performance_rating": perf,
                "status": status,
                "leave_balance": leave_bal,
            }
        )

    # --- Generate EMP016–EMP100 ---
    dept_pool = []
    for dept, count in DEPARTMENTS.items():
        dept_pool.extend([dept] * count)

    generated = 0
    idx = 16
    while generated < 85:
        emp_id = f"EMP{idx:03d}"
        dept = dept_pool[generated % len(dept_pool)]
        pos_list = POSITIONS[dept]
        pos = random.choice(pos_list)
        gender = random.choice(["M", "M", "F"])
        name = gen_name(gender)
        level = pick_level(pos)
        sal_csv = random.randint(800, 5000)  # CSV salary column
        sal_vnd = gen_salary(level)
        hire = rand_date(date(2018, 1, 1), date(2025, 12, 31))
        status = random.choices(["Active", "Resigned"], weights=[88, 12])[0]
        perf = round(random.uniform(3.0, 5.0), 1)
        leave_bal = random.randint(0, 25) if status == "Active" else 0
        contract = gen_contract_dates(hire)
        skills = gen_skills(dept)

        # Assign dept manager from generated pool if not yet set
        if DEPT_MANAGER.get(dept) is None and "manager" in pos.lower():
            DEPT_MANAGER[dept] = emp_id

        emp = {
            "employee_id": emp_id,
            "name": name,
            "gender": gender,
            "department": dept,
            "position": pos,
            "level": level,
            "email": gen_email(name, emp_id),
            "phone": gen_phone(),
            "hire_date": str(hire),
            "status": status,
            "manager_id": DEPT_MANAGER.get(dept)
            if emp_id != DEPT_MANAGER.get(dept)
            else None,
            "salary_vnd": sal_vnd,
            "leave_balance": leave_bal,
            "performance_rating": perf,
            "skills": skills,
            "contract": contract,
            "address": f"Quận {random.randint(1, 12)}, TP.HCM",
            "emergency_contact": {
                "name": gen_name("F"),
                "phone": gen_phone(),
                "relation": "Family",
            },
            "education": random.choice(["Đại học", "Thạc sĩ", "Cao đẳng", "Đại học"]),
        }
        employees_json.append(emp)
        csv_rows.append(
            {
                "employee_id": emp_id,
                "name": name,
                "department": dept,
                "position": pos,
                "salary": sal_csv,
                "hire_date": str(hire),
                "performance_rating": perf,
                "status": status,
                "leave_balance": leave_bal,
            }
        )
        idx += 1
        generated += 1

    return employees_json, csv_rows


def build_appraisals(employees: list[dict]) -> dict:
    """Generate appraisal records for active employees."""
    active = [e for e in employees if e["status"] == "Active"][:20]
    records = []
    periods = ["2025-H1", "2025-H2", "2026-H1"]
    types = ["Annual", "Semi-annual", "Probation"]
    for emp in active:
        period = random.choice(periods)
        appraisal_type = random.choice(types)
        self_score = round(random.uniform(3.5, 5.0), 1)
        mgr_score = round(random.uniform(3.0, 5.0), 1)
        final_score = round((self_score * 0.3 + mgr_score * 0.7), 1)
        status = random.choice(["Completed", "In Progress", "Pending"])
        records.append(
            {
                "appraisal_id": f"APR-{period}-{emp['employee_id']}",
                "employee_id": emp["employee_id"],
                "employee_name": emp["name"],
                "department": emp["department"],
                "position": emp["position"],
                "manager_id": emp.get("manager_id"),
                "period": period,
                "type": appraisal_type,
                "status": status,
                "self_evaluation": {
                    "score": self_score,
                    "achievements": "Hoàn thành các mục tiêu Q1, dẫn dắt 2 dự án thành công.",
                    "challenges": "Gặp khó khăn về tài nguyên và deadline chồng chéo.",
                    "goals_next": "Nâng cao kỹ năng leadership và hoàn thành chứng chỉ chuyên môn.",
                    "submitted_at": f"2026-{random.randint(1, 5):02d}-{random.randint(1, 28):02d}T09:00:00",
                },
                "manager_feedback": {
                    "score": mgr_score,
                    "strengths": "Làm việc chăm chỉ, kỹ năng chuyên môn tốt.",
                    "improvements": "Cần cải thiện kỹ năng giao tiếp và quản lý thời gian.",
                    "submitted_at": f"2026-{random.randint(1, 5):02d}-{random.randint(1, 28):02d}T14:00:00"
                    if status == "Completed"
                    else None,
                },
                "final_score": final_score if status == "Completed" else None,
                "rating_label": (
                    "Xuất sắc"
                    if final_score and final_score >= 4.5
                    else "Tốt"
                    if final_score and final_score >= 4.0
                    else "Đạt yêu cầu"
                    if final_score and final_score >= 3.0
                    else "Cần cải thiện"
                )
                if status == "Completed"
                else None,
                "created_at": f"2026-{random.randint(1, 3):02d}-01T08:00:00",
            }
        )
    return {"appraisals": records, "total": len(records)}


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(base, exist_ok=True)

    employees, csv_rows = build_employees()

    # 1. employees_data.json
    emp_path = os.path.join(base, "employees_data.json")
    with open(emp_path, "w", encoding="utf-8") as f:
        json.dump(
            {"employees": employees, "total": len(employees)},
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"[OK] {emp_path}  ({len(employees)} employees)")

    # 2. hr_mock_data.csv
    csv_path = os.path.join(base, "hr_mock_data.csv")
    fieldnames = [
        "employee_id",
        "name",
        "department",
        "position",
        "salary",
        "hire_date",
        "performance_rating",
        "status",
        "leave_balance",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"[OK] {csv_path}  ({len(csv_rows)} rows)")

    # 3. appraisal_data.json
    appraisal_data = build_appraisals(employees)
    apr_path = os.path.join(base, "appraisal_data.json")
    with open(apr_path, "w", encoding="utf-8") as f:
        json.dump(appraisal_data, f, ensure_ascii=False, indent=2)
    print(f"[OK] {apr_path}  ({appraisal_data['total']} appraisals)")

    print("\nAll data files generated successfully!")
