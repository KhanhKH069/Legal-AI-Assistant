"""
Employee Portal - Onboarding Checklist & Document Upload
Add this to your Streamlit app
"""

import streamlit as st
import time


def show_employee_portal():
    """Display Employee Portal with Onboarding tasks"""

    st.markdown("##  Employee Portal - My Onboarding")

    # Mock user login
    st.info(" Welcome! You are logged in as **EMP003 - Le Thi C** (New Employee)")

    # Progress
    st.markdown("###  Onboarding Progress")
    st.progress(30)
    st.caption("30% Completed")

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("###  My Tasks")

        # Day 1 tasks
        st.markdown("#### Day 1")
        st.checkbox("Read Company Culture & Values", value=True, disabled=True)
        st.checkbox("Setup Email & Slack", value=True, disabled=True)
        st.checkbox("Meet the Team (1-on-1 with Manager)", value=False)

        # Week 1 tasks
        st.markdown("#### Week 1")
        st.checkbox("Complete Security Training", value=False)
        st.checkbox("Submit Personal Documents", value=False)

    with col2:
        st.markdown("###  Document Upload")
        st.markdown("Please upload the required documents.")

        doc_type = st.selectbox(
            "Document Type",
            ["Citizen ID (CCCD)", "Tax Registration", "Health Check Certificate"],
        )
        uploaded_doc = st.file_uploader(
            f"Upload {doc_type} (Image/PDF)", type=["png", "jpg", "jpeg", "pdf"]
        )

        if st.button("Submit Document", use_container_width=True):
            if uploaded_doc:
                with st.spinner("Phân tích AI đang kiểm tra tài liệu..."):
                    time.sleep(2)  # Mock OCR processing time

                    # Mock AI OCR validation logic
                    if "CCCD" in doc_type:
                        st.success(" Document Verified: Valid Citizen ID detected.")
                        st.balloons()
                    else:
                        st.success(
                            f" {doc_type} uploaded successfully and sent to HR for review."
                        )
            else:
                st.error("Please upload a file first.")

    st.markdown("---")
    st.markdown("###  Onboarding Assistant")
    st.markdown(
        "Bạn có câu hỏi nào về quy trình Onboarding không? Hãy sang tab **HR Assistant** để hỏi nhé!"
    )


# ============================================
# ADD TO YOUR STREAMLIT APP
# ============================================

if __name__ == "__main__":
    st.set_page_config(page_title="Employee Portal", layout="wide")
    show_employee_portal()
