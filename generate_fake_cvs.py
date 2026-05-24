import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_pdf(filename, name, position, experience, skills, education, projects):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Name & Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, name)
    c.setFont("Helvetica", 14)
    c.drawString(50, height - 75, position)

    # Skills
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 120, "TECHNICAL SKILLS")
    c.setFont("Helvetica", 10)
    skill_text = ", ".join(skills)
    c.drawString(50, height - 140, skill_text)

    # Experience
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 180, "EXPERIENCE")
    c.setFont("Helvetica", 10)
    y = height - 200
    for exp in experience:
        c.drawString(50, y, exp)
        y -= 20

    # Education
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 20, "EDUCATION")
    c.setFont("Helvetica", 10)
    c.drawString(50, y - 40, education)

    # Projects
    c.setFont("Helvetica-Bold", 12)
    y -= 80
    c.drawString(50, y, "PROJECTS")
    c.setFont("Helvetica", 10)
    y -= 20
    for proj in projects:
        c.drawString(50, y, proj)
        y -= 20

    c.save()


def generate_fake_cvs():
    cvs = [
        {
            "name": "Ngo Van B",
            "position": "AI Engineer Intern",
            "experience": [
                "2023 - Present: Student at ABC University",
                "Machine Learning class project",
            ],
            "skills": ["Python", "C++", "Math", "Basic Machine Learning", "Git"],
            "education": "B.S. in Computer Science (Expected 2025)",
            "projects": [
                "- Digit Recognizer using KNN",
                "- Simple Chatbot with Python",
            ],
            "filename": "data/cv_uploads/Intern_NgoVanB.pdf",
        },
        {
            "name": "Le Thi C",
            "position": "AI Engineer Junior",
            "experience": [
                "2022 - 2024: AI Researcher Assistant",
                "2024 - Present: Junior Data Scientist at XYZ Corp",
            ],
            "skills": [
                "Python",
                "TensorFlow",
                "PyTorch",
                "SQL",
                "Pandas",
                "Scikit-Learn",
                "Docker",
            ],
            "education": "B.S. in Data Science (2022)",
            "projects": [
                "- Recommendation System for E-commerce (PyTorch)",
                "- Customer Churn Prediction model",
            ],
            "filename": "data/cv_uploads/Junior_LeThiC.pdf",
        },
        {
            "name": "Tran Van D",
            "position": "AI Engineer Senior",
            "experience": [
                "2018 - 2020: Software Engineer at FPT",
                "2020 - 2023: AI Engineer at VNG",
                "2023 - Present: Lead AI Engineer at TechStart",
            ],
            "skills": [
                "Python",
                "PyTorch",
                "Transformers",
                "LLMs",
                "LangChain",
                "Kubernetes",
                "AWS SageMaker",
                "MLOps",
                "FastAPI",
            ],
            "education": "Master in Computer Science, specialized in AI (2020)",
            "projects": [
                "- Built RAG system supporting 10k CCU using Llama-3",
                "- Scaled inference pipeline with TensorRT and Triton",
                "- Automated MLOps CI/CD pipelines",
            ],
            "filename": "data/cv_uploads/Senior_TranVanD.pdf",
        },
        {
            "name": "Hoang Thi E",
            "position": "Frontend Developer Middle",
            "experience": [
                "2021 - 2023: Junior Frontend at Shopee",
                "2023 - Present: Mid-level Frontend at Grab",
            ],
            "skills": [
                "JavaScript",
                "TypeScript",
                "React",
                "Next.js",
                "TailwindCSS",
                "Redux",
                "Jest",
            ],
            "education": "B.S. in Information Technology (2021)",
            "projects": [
                "- Rebuilt vendor dashboard using Next.js 13",
                "- Optimized Core Web Vitals to 90+ score",
            ],
            "filename": "data/cv_uploads/Frontend_Middle_HoangThiE.pdf",
        },
        {
            "name": "Pham Van F",
            "position": "Backend Developer Fresher",
            "experience": ["2023: Internship at VNPAY"],
            "skills": ["Java", "Spring Boot", "MySQL", "Git", "REST API"],
            "education": "B.S. in Software Engineering (2023)",
            "projects": [
                "- E-commerce API with Spring Boot and JWT Auth",
                "- Database optimization for user queries",
            ],
            "filename": "data/cv_uploads/Backend_Fresher_PhamVanF.pdf",
        },
    ]

    for cv in cvs:
        create_pdf(
            filename=cv["filename"],
            name=cv["name"],
            position=cv["position"],
            experience=cv["experience"],
            skills=cv["skills"],
            education=cv["education"],
            projects=cv["projects"],
        )
        print(f"Generated {cv['filename']}")


if __name__ == "__main__":
    generate_fake_cvs()
