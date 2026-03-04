"""
HR Dashboard - View CV Screening Results
Add this to your Streamlit app
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st


def show_hr_dashboard():
    """Display HR dashboard with CV screening results"""

    st.markdown("##  HR Dashboard - CV Screening Results")

    # Check if screening has been run
    screening_file = Path("screening_results.json")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.info(" Hệ thống tự động phân tích CV dựa trên skills, experience, education")

    with col2:
        if st.button(" Run Screening", use_container_width=True):
            with st.spinner("Đang phân tích CV..."):
                # Import screening module
                from cv_screening import export_screening_results, screen_all_applicants

                results = screen_all_applicants()

                if results:
                    export_screening_results(results)
                    st.success(f" Đã phân tích {len(results)} CV!")
                    st.rerun()
                else:
                    st.warning("Chưa có CV nào để phân tích")

    st.markdown("---")

    # Load results
    if screening_file.exists():
        with open(screening_file, "r", encoding="utf-8") as f:
            results = json.load(f)

        if not results:
            st.warning("Chưa có kết quả phân tích")
            return

        # Summary stats
        st.markdown("###  Tổng Quan")

        col1, col2, col3, col4 = st.columns(4)

        total = len(results)
        strong_pass = len([r for r in results if r["recommendation"] == "STRONG_PASS"])
        passed = len(
            [r for r in results if r["recommendation"] in ["STRONG_PASS", "PASS"]]
        )
        rejected = len([r for r in results if r["recommendation"] == "REJECT"])

        with col1:
            st.metric(" Tổng CV", total)
        with col2:
            st.metric(" Xuất Sắc", strong_pass)
        with col3:
            st.metric(" Đạt", passed)
        with col4:
            st.metric(" Không Đạt", rejected)

        st.markdown("---")

        # Filter by recommendation
        st.markdown("###  Lọc Ứng Viên")

        filter_option = st.selectbox(
            "Hiển thị:",
            [
                "Tất cả",
                " Highly Recommended",
                " Recommended",
                " Consider",
                " Not Recommended",
            ],
        )

        # Filter results
        if filter_option != "Tất cả":
            if "Highly" in filter_option:
                filtered = [r for r in results if r["recommendation"] == "STRONG_PASS"]
            elif "Recommended" in filter_option:
                filtered = [r for r in results if r["recommendation"] == "PASS"]
            elif "Consider" in filter_option:
                filtered = [r for r in results if r["recommendation"] == "MAYBE"]
            else:
                filtered = [r for r in results if r["recommendation"] == "REJECT"]
        else:
            filtered = results

        st.markdown(f"**Hiển thị {len(filtered)} / {total} ứng viên**")

        # Display results
        for i, result in enumerate(filtered, 1):
            with st.expander(
                f"{i}. {result['name']} - {result['position']} | Score: {result['total_score']}/100 ({result['percentage']}%)",
                expanded=(i <= 3),  # Auto-expand top 3
            ):
                # Header info
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"** Email:** {result['email']}")
                    st.markdown(f"** Phone:** {result['phone']}")

                with col2:
                    st.markdown(f"** Vị trí:** {result['position']}")
                    st.markdown(f"** Nộp:** {result.get('timestamp', 'N/A')}")

                with col3:
                    # Status badge
                    status = result["status"]
                    if "" in status:
                        st.success(status)
                    elif "" in status:
                        st.warning(status)
                    else:
                        st.error(status)

                    st.info(f"**Action:** {result['action']}")

                st.markdown("---")

                # Score breakdown
                st.markdown("####  Chi Tiết Điểm")

                breakdown = result["breakdown"]

                # Required skills
                req_skills = breakdown["required_skills"]
                st.markdown(f"**1. Required Skills** ({req_skills['points']:.1f}/30)")
                st.progress(req_skills["percentage"] / 100)
                st.caption(
                    f" Found: {', '.join(req_skills['found']) if req_skills['found'] else 'None'}"
                )

                # Preferred skills
                pref_skills = breakdown["preferred_skills"]
                st.markdown(f"**2. Preferred Skills** ({pref_skills['points']:.1f}/20)")
                st.progress(pref_skills["percentage"] / 100)
                st.caption(
                    f" Found: {', '.join(pref_skills['found']) if pref_skills['found'] else 'None'}"
                )

                # Experience
                exp = breakdown["experience"]
                st.markdown(f"**3. Experience** ({exp['points']}/25)")
                st.caption(
                    f" {exp['years_found']} years (required: {exp['years_required']})"
                )

                # Education
                edu = breakdown["education"]
                st.markdown(f"**4. Education** ({edu['points']}/15)")
                st.caption(f"{'' if edu['relevant'] else ''} Relevant education")

                # Certifications
                certs = breakdown["certifications"]
                st.markdown(f"**5. Certifications** ({certs['points']}/10)")
                st.caption(
                    f" Found: {', '.join(certs['found']) if certs['found'] else 'None'}"
                )

                st.markdown("---")

                # Actions
                st.markdown("####  Hành Động Tuyển Dụng")
                colA, colB, colC = st.columns(3)

                with colA:
                    if st.button(" Xem Email Mẫu", key=f"email_{i}"):
                        st.session_state[f"show_email_{i}"] = True

                with colB:
                    if st.button(" View CV", key=f"cv_{i}"):
                        st.info(f"CV location: {result['cv_path']}")

                with colC:
                    if st.button(" Schedule Interview", key=f"interview_{i}"):
                        from src.tools.email_calendar_tools import schedule_google_meet

                        meet_link = schedule_google_meet([result["email"]])
                        st.success(
                            f" Đã xếp lịch online lúc 14:00 ngày mai. Link: {meet_link}"
                        )
                        st.balloons()

                # Email Preview Expander (chỉ hiện khi click)
                if st.session_state.get(f"show_email_{i}", False):
                    with st.expander(" Email Preview", expanded=True):
                        from src.tools.email_calendar_tools import draft_interview_email

                        # Mock time
                        draft = draft_interview_email(
                            result["name"], result["position"], "14:00 Ngày mai"
                        )
                        st.text_area(
                            "Nội dung Email (AI Sinh)",
                            value=draft,
                            height=250,
                            key=f"text_{i}",
                        )
                        if st.button(" Gửi Email", key=f"send_{i}"):
                            st.success(f" Đã gửi email tới {result['email']}!")
                            st.session_state[f"show_email_{i}"] = False
                            st.rerun()

        # Export option
        st.markdown("---")

        if st.button(" Export to Excel"):
            # Convert to DataFrame
            df_data = []
            for r in results:
                df_data.append(
                    {
                        "Name": r["name"],
                        "Email": r["email"],
                        "Phone": r["phone"],
                        "Position": r["position"],
                        "Score": r["total_score"],
                        "Percentage": r["percentage"],
                        "Status": r["status"],
                        "Action": r["action"],
                        "Timestamp": r.get("timestamp", "N/A"),
                    }
                )

            df = pd.DataFrame(df_data)

            # Save to Excel (requires openpyxl)
            excel_file = "screening_results.xlsx"
            df.to_excel(excel_file, index=False)

            st.success(f" Exported to {excel_file}")

    else:
        st.warning(" Chưa có kết quả phân tích. Click 'Run Screening' để bắt đầu!")


# ============================================
# ADD TO YOUR STREAMLIT APP
# ============================================

if __name__ == "__main__":
    st.set_page_config(page_title="HR Dashboard", layout="wide")
    show_hr_dashboard()
