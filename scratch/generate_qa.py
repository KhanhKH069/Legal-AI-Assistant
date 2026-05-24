import json
import os


def generate_qa():
    # Load config
    config_path = os.path.join(
        "d:\\hr-ai-agent-pure-vector", "job_requirements_config.json"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    out_path = os.path.join(
        "d:\\hr-ai-agent-pure-vector", "documents", "02_Job_Requirements.md"
    )

    lines = ["# Job Requirements Q&A\n\n"]

    for i, (pos, details) in enumerate(config.items(), 1):
        lines.append(f"### Q{i}:")
        lines.append(f"**Câu hỏi:** Yêu cầu cho vị trí {pos}?")

        # Variations
        lines.append("**Biến thể:**")
        lines.append(f"- Yêu cầu tuyển dụng {pos} là gì?")
        lines.append(f"- {pos} cần những kỹ năng gì?")
        lines.append(f"- Tiêu chí tuyển {pos}")
        lines.append(f"- Job description cho {pos}")

        # Answer
        lines.append("**Trả lời:**")
        lines.append(f"Yêu cầu cho vị trí {pos}:")

        req = details.get("technical_skills", {}).get("required", {})
        if req.get("skills"):
            lines.append("- Kỹ năng bắt buộc: " + ", ".join(req["skills"]))

        pref = details.get("technical_skills", {}).get("preferred", {})
        if pref.get("skills"):
            lines.append("- Kỹ năng ưu tiên: " + ", ".join(pref["skills"]))

        exp = details.get("experience", {})
        if "min_years" in exp:
            lines.append(f"- Kinh nghiệm: Ít nhất {exp['min_years']} năm")

        edu = details.get("education", {})
        if edu.get("required_degree"):
            lines.append(
                "- Học vấn: "
                + edu["required_degree"]
                + (
                    " (Các ngành: " + ", ".join(edu.get("preferred_majors", [])) + ")"
                    if edu.get("preferred_majors")
                    else ""
                )
            )

        cert = details.get("certifications", {})
        if cert.get("nice_to_have"):
            lines.append("- Chứng chỉ: " + ", ".join(cert["nice_to_have"]))

        lines.append("\n---\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Generated {len(config)} Q&A pairs in {out_path}")


if __name__ == "__main__":
    generate_qa()
