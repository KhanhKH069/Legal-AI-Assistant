#!/usr/bin/env python3
"""
Paraline HR Assistant
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
load_dotenv()

st.set_page_config(
    page_title="Paraline HR Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="auto"
)

# CSS (same as before)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: 'Poppins', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header {visibility: hidden;}
    
    .stApp {
        background: #ffffff;
    }
    
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    
    /* Navbar */
    .navbar {
        background: white;
        padding: 20px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    
    .nav-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 40px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .logo {
        font-size: 32px;
        font-weight: 700;
        color: #333;
    }
    
    .logo span {
        color: #4CAF50;
    }
    
    .nav-links {
        display: flex;
        gap: 40px;
    }
    
    .nav-links a {
        color: #666;
        text-decoration: none;
        font-size: 15px;
        transition: color 0.3s;
    }
    
    .nav-links a:hover, .nav-links a.active {
        color: #4CAF50;
        border-bottom: 2px solid #4CAF50;
    }
    
    /* Hero */
    .hero {
        text-align: center;
        padding: 80px 40px;
        background: white;
    }
    
    .hero h1 {
        font-size: 48px;
        font-weight: 300;
        color: #555;
        margin-bottom: 30px;
    }
    
    .hero h1 .highlight {
        color: #4CAF50;
        font-weight: 600;
    }
    
    .hero p {
        font-size: 18px;
        color: #777;
        max-width: 800px;
        margin: 0 auto;
        line-height: 1.8;
    }
    
    /* Chat */
    .chat-section {
        max-width: 900px;
        margin: 0 auto;
        padding: 0 40px 80px 40px;
    }
    
    .chat-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .chat-header {
        text-align: center;
        padding-bottom: 20px;
        border-bottom: 1px solid #f0f0f0;
        margin-bottom: 20px;
    }
    
    .chat-header h2 {
        font-size: 24px;
        font-weight: 500;
        color: #333;
    }
    
    /* Messages */
    .stChatMessage {
        padding: 12px 16px !important;
        margin-bottom: 10px !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: #333333 !important;
    }
    
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p {
        color: white !important;
    }
    
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: #f5f5f5 !important;
    }
    
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) *,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) p,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) strong,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) li,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) span,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) div,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) ul,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) code {
        color: #333333 !important;
    }
    
    /* Input */
    .stChatInput {
        margin-top: 20px;
    }
    
    .stChatInput > div {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
    
    .stChatInput input {
        border: none !important;
        padding: 12px 16px !important;
    }
    
    /* Footer */
    .paraline-footer {
        background: #f5f7fa;
        padding: 60px 40px 30px 40px;
        margin-top: 80px;
    }
    
    .footer-logo {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .footer-logo h2 {
        font-size: 36px;
        font-weight: 700;
        color: #333;
    }
    
    .footer-logo h2 span {
        color: #4CAF50;
    }
    
    .footer-nav {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .footer-nav a {
        color: #999;
        text-decoration: none;
        margin: 0 20px;
        font-size: 15px;
    }
    
    .footer-contact {
        text-align: center;
        color: #999;
        font-size: 14px;
        margin-bottom: 30px;
    }
    
    .footer-contact span {
        margin: 0 20px;
    }
    
    .footer-divider {
        width: 200px;
        height: 2px;
        background: #4CAF50;
        margin: 30px auto;
    }
    
    .footer-bottom {
        text-align: center;
        color: #999;
        font-size: 14px;
    }
    
    .footer-bottom .heart {
        color: #e74c3c;
    }
    
    /* Sidebar upload */
    [data-testid="stSidebar"] .stFileUploader {
        background: white;
        border: 2px dashed #4CAF50;
        border-radius: 8px;
        padding: 1rem;
    }
    
    [data-testid="stSidebar"] .stFileUploader label {
        color: #4CAF50;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CV MANAGEMENT FUNCTIONS
# ============================================

def save_cv_to_disk(uploaded_file, applicant_info):
    """Save CV to uploads folder"""
    try:
        # Create uploads directory
        upload_dir = Path("cv_uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{applicant_info['name']}_{uploaded_file.name}"
        filepath = upload_dir / filename
        
        # Save file
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return str(filepath)
    except Exception as e:
        st.error(f"❌ Lỗi lưu file: {e}")
        return None

def save_to_database(applicant_info):
    """Save applicant info to JSON database"""
    try:
        db_file = Path("applicants_db.json")
        
        # Load existing data
        if db_file.exists() and db_file.stat().st_size > 0:
            try:
                with open(db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                # File exists but empty or corrupted
                data = []
        else:
            data = []
        
        # Add new applicant
        data.append(applicant_info)
        
        # Save
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        st.error(f"❌ Lỗi lưu database: {e}")
        return False

def send_email_notification(applicant_info):
    """Send email to HR"""
    try:
        # TODO: Configure SMTP settings in .env
        # For now, just log the action
        email_log = Path("email_notifications.log")
        
        with open(email_log, 'a', encoding='utf-8') as f:
            f.write("\n--- New Application ---\n")
            f.write(f"Time: {applicant_info['timestamp']}\n")
            f.write(f"Name: {applicant_info['name']}\n")
            f.write(f"Email: {applicant_info['email']}\n")
            f.write(f"Phone: {applicant_info['phone']}\n")
            f.write(f"Position: {applicant_info['position']}\n")
            f.write(f"CV: {applicant_info['cv_path']}\n")
            f.write("------------------------\n")
        
        return True
    except Exception as e:
        st.error(f"⚠️ Email notification failed: {e}")
        return False

# ============================================
# HELPER FUNCTIONS
# ============================================

def validate_match(user_q, matched_q, dist):
    if dist < 0.5:
        return True
    user_w = set(user_q.lower().split())
    match_w = set(matched_q.lower().split())
    stop = {'là', 'có', 'được', 'không', 'gì', 'như', 'thế', 'nào', 'bao', 'nhiêu'}
    common = (user_w - stop) & (match_w - stop)
    return len(common) >= (1 if dist < 0.6 else 2)

def query_vector_db(q):
    try:
        from services.vector_db import get_vector_db
        vdb = get_vector_db()
        res = vdb.query(collection_name='hr_policies', query_text=q, n_results=3)
        
        if res and res['documents'] and len(res['documents'][0]) > 0:
            for i in range(len(res['documents'][0])):
                meta = res['metadatas'][0][i]
                dist = res['distances'][0][i] if 'distances' in res else 1.0

                if dist >= 0.7:
                    continue

                mq = meta.get('question', '')
                if not validate_match(q, mq, dist):
                    continue
                
                return {
                    'found': True,
                    'answer': meta.get('answer', ''),
                    'question': mq,
                    'source': meta.get('source_file', ''),
                    'similarity': round((1 - dist) * 100, 1),
                    'distance': dist
                }
        return {'found': False}
    except Exception as e:
        return {'found': False, 'error': str(e)}

# ============================================
# SESSION STATE
# ============================================

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": """<div style="color: #333;">
<span style="color: #333;">👋 <strong>Xin chào! Tôi là HR Assistant của Paraline.</strong></span><br><br>
<span style="color: #333;">Tôi có thể giúp bạn với các câu hỏi về công ty Paraline Software.</span><br><br>
</div>"""
    }]

if 'stats' not in st.session_state:
    st.session_state.stats = {'found': 0, 'not_found': 0, 'total': 0}

if 'debug' not in st.session_state:
    st.session_state.debug = False

# ============================================
# NAVIGATION
# ============================================

st.markdown("""
<div class="navbar">
    <div class="nav-container">
        <div class="logo">Para<span>line</span></div>
        <div class="nav-links">
            <a href="#home">TRANG CHỦ</a>
            <a href="#chat" class="active">HR Assistant</a>
            <a href="#about">Thông tin</a>
            <a href="#contact">Liên hệ</a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# HERO
# ============================================

st.markdown("""
<div class="hero" id="home">
    <h1>Welcome to <span class="highlight">Paraline</span> HR Assistant</h1>
    <p>Paraline được sáng lập bởi những thành viên từng học tập, làm việc tại Nhật Bản. 
    Chúng tôi hứa sẽ cung cấp đến khách hàng những sản phẩm có <strong>「Japan Quality」</strong> tại Việt Nam. 
    Hệ thống HR Assistant giúp nhân viên tra cứu thông tin nhanh chóng, chính xác.</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# CHAT
# ============================================

st.markdown('<div class="chat-section" id="chat">', unsafe_allow_html=True)
st.markdown('<div class="chat-card">', unsafe_allow_html=True)

st.markdown("""
<div class="chat-header">
    <h2>💬 Trò chuyện với HR Assistant</h2>
</div>
""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        with st.spinner("Đang tìm kiếm..."):
            result = query_vector_db(prompt)
        
        st.session_state.stats['total'] += 1
        
        if result['found']:
            answer = result['answer']
            lines = answer.split('\n')
            formatted_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith('- ') or line.startswith('• '):
                    content = line[2:] if line.startswith('- ') else line[2:]
                    formatted_lines.append(f'<span style="color: #333;">• {content}</span>')
                elif line:
                    formatted_lines.append(f'<span style="color: #333;">{line}</span>')
                else:
                    formatted_lines.append('<br>')
            
            answer_html = '<br>'.join(formatted_lines)
            resp = f'<div style="color: #333;"><strong>📚 Trả lời:</strong><br><br>{answer_html}</div>'
            
            if st.session_state.debug:
                resp += f"<br><br><small style='color: #666;'>📄 {result['source']} | 🎯 {result['similarity']}%</small>"
            
            placeholder.markdown(resp, unsafe_allow_html=True)
            st.session_state.stats['found'] += 1
        else:
            resp = '<div style="color: #333;">❌ <strong>Không tìm thấy</strong><br><br>Xin lỗi, câu hỏi này chưa có trong knowledge base.<br><br>💡 Vui lòng liên hệ HR: <strong>hr@paraline.com.vn</strong></div>'
            placeholder.markdown(resp, unsafe_allow_html=True)
            st.session_state.stats['not_found'] += 1
        
        st.session_state.messages.append({"role": "assistant", "content": resp})

st.markdown('</div></div>', unsafe_allow_html=True)

# ============================================
# FOOTER
# ============================================

footer_html = """
<style>
.paraline-footer {
    background: #f5f7fa;
    padding: 60px 40px 30px 40px;
    margin: 0;
    font-family: 'Poppins', sans-serif;
}

.footer-logo {
    text-align: center;
    margin-bottom: 30px;
}

.footer-logo h2 {
    font-size: 36px;
    font-weight: 700;
    color: #333;
    margin: 0;
}

.footer-logo h2 span {
    color: #4CAF50;
}

.footer-nav {
    text-align: center;
    margin-bottom: 30px;
}

.footer-nav a {
    color: #999;
    text-decoration: none;
    margin: 0 30px;
    font-size: 15px;
}

.footer-contact {
    text-align: center;
    color: #999;
    font-size: 14px;
    margin-bottom: 30px;
}

.footer-contact span {
    margin: 0 30px;
}

.footer-divider {
    width: 200px;
    height: 2px;
    background: #4CAF50;
    margin: 30px auto;
}

.footer-bottom {
    text-align: center;
    color: #999;
    font-size: 14px;
}

.footer-bottom .heart {
    color: #e74c3c;
}
</style>

<div class="paraline-footer">
    <div class="footer-logo">
        <h2>Para<span>line</span></h2>
    </div>
    
    <div class="footer-nav">
        <a href="#home">Home</a>
        <a href="#services">Services</a>
        <a href="#about">About us</a>
        <a href="#contact">Contact</a>
    </div>
    
    <div class="footer-contact">
        <span>info@paraline.com.vn</span>
        <span>+84 24-3200-4679</span>
    </div>
    
    <div class="footer-divider"></div>
    
    <div class="footer-bottom">
        © 2017. Made with <span class="heart">❤️</span> in Hanoi
    </div>
</div>
"""

components.html(footer_html, height=400)

# ============================================
# SIDEBAR - CV UPLOAD
# ============================================

with st.sidebar:
    st.markdown("### 💼 Ứng Tuyển Việc Làm - Apply for jobs")
    
    with st.form("cv_form", clear_on_submit=True):
        st.markdown("**📄 Thông tin ứng viên**")
        
        name = st.text_input("Họ và tên - Fullname *", placeholder="")
        email = st.text_input("Email *", placeholder="")
        phone = st.text_input("Số điện thoại - Contact*", placeholder="")
        
        position = st.selectbox(
            "Vị trí ứng tuyển *",
            [
                "-- Chọn vị trí --",
                "Software Engineer",
                "Frontend Developer", 
                "Backend Developer",
                "QA Engineer",
                "Project Manager",
                "Business Analyst",
                "HR Specialist",
                "AI Engineer",
                "AI Intern",
                "DevOps Engineer",
                "Devops Intern"
            ]
        )
        
        uploaded_cv = st.file_uploader(
            "Upload CV (PDF, DOCX) *", 
            type=['pdf', 'docx', 'doc'],
            help="Kích thước tối đa: 10MB"
        )
        
        submitted = st.form_submit_button("📤 Nộp Hồ Sơ", use_container_width=True)
        
        if submitted:
            # Validate
            if not name or not email or not phone:
                st.error("❌ Vui lòng điền đầy đủ thông tin!")
            elif position == "-- Chọn vị trí --":
                st.error("❌ Vui lòng chọn vị trí ứng tuyển!")
            elif not uploaded_cv:
                st.error("❌ Vui lòng upload CV!")
            else:
                # Process application
                with st.spinner("Đang xử lý..."):
                    # Save CV
                    applicant_info = {
                        'name': name,
                        'email': email,
                        'phone': phone,
                        'position': position,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'cv_filename': uploaded_cv.name
                    }
                    
                    cv_path = save_cv_to_disk(uploaded_cv, applicant_info)
                    
                    if cv_path:
                        applicant_info['cv_path'] = cv_path
                        
                        # Save to database
                        db_saved = save_to_database(applicant_info)
                        
                        # Send email notification
                        email_sent = send_email_notification(applicant_info)
                        
                        if db_saved:
                            st.success("✅ Đã nộp CV thành công!")
                            st.success(f"🎯 Vị trí: **{position}**")
                            st.info("📧 HR sẽ liên hệ với bạn trong 3-5 ngày làm việc!")
                            st.balloons()
                        else:
                            st.warning("⚠️ CV đã được lưu nhưng có lỗi với database")
    
    st.markdown("---")
    st.markdown("### 🔧 Developer")
    debug = st.checkbox("Debug", value=st.session_state.debug)
    st.session_state.debug = debug
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅", st.session_state.stats['found'])
    with col2:
        st.metric("❌", st.session_state.stats['not_found'])
    
    if st.button("🔄 Clear"):
        st.session_state.messages = st.session_state.messages[:1]
        st.session_state.stats = {'found': 0, 'not_found': 0, 'total': 0}
        st.rerun()