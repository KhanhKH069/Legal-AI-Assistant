import json
from cv_screening import score_cv

cvs = [
    r"D:\hr-ai-agent-pure-vector\cv_uploads\CV_PhamHaLinh.pdf",
    r"D:\hr-ai-agent-pure-vector\cv_uploads\Vu_Nam_Khanh_cv.pdf",
]

position = "AI Engineer - Intern"

for cv in cvs:
    print(f"=== Evaluating {cv} for {position} ===")
    try:
        res = score_cv(cv, position)
        if "error" in res:
            print("Error:", res["error"])
        else:
            print(f"Total Score: {res.get('total_score', 0)}")
            print("Breakdown:")
            print(json.dumps(res.get("breakdown", {}), indent=2))
            print("Raw Skills extracted:", len(res.get("raw_skills", "")))
            print("Raw Projects extracted:", len(res.get("raw_projects", "")))
    except Exception as e:
        print("Exception:", e)
    print("\n")
