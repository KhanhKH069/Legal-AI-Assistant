"""
Job Requirements Configuration Manager
Allows HR to customize requirements for each position
"""

import json
from pathlib import Path
from typing import Dict

import streamlit as st

# ============================================
# DEFAULT PARALINE JOB REQUIREMENTS
# ============================================

DEFAULT_REQUIREMENTS = {
    "Software Engineer": {
        "position_info": {
            "title": "Software Engineer",
            "department": "Engineering",
            "level": "Mid-Senior",
            "salary_range": "15-30 triệu VND"
        },
        
        "technical_skills": {
            "required": {
                "programming": ["Python", "JavaScript", "Java"],
                "databases": ["SQL", "PostgreSQL", "MongoDB"],
                "tools": ["Git", "Docker", "Linux"],
                "frameworks": ["Django/Flask", "React/Vue", "REST API"]
            },
            "preferred": {
                "cloud": ["AWS", "Azure", "GCP"],
                "devops": ["Kubernetes", "Jenkins", "CI/CD"],
                "testing": ["Pytest", "Jest", "Unit Testing"],
                "other": ["Microservices", "GraphQL", "Redis"]
            },
            "weight": 50  # 50% of total score
        },
        
        "experience": {
            "min_years": 2,
            "max_years": 8,
            "preferred_years": 3,
            "industries": ["Software", "Fintech", "E-commerce"],
            "specific_experience": [
                "Full-stack development",
                "API design & development",
                "Database optimization",
                "Team collaboration"
            ],
            "weight": 25  # 25% of total score
        },
        
        "education": {
            "required_degree": "Bachelor",
            "preferred_majors": [
                "Computer Science",
                "Software Engineering",
                "Information Technology",
                "Computer Engineering"
            ],
            "alternative_majors": [
                "Mathematics",
                "Physics",
                "Electronics"
            ],
            "bootcamp_acceptable": True,
            "weight": 10  # 10% of total score
        },
        
        "certifications": {
            "preferred": [
                "AWS Certified Developer",
                "Google Cloud Professional",
                "Oracle Certified Professional",
                "Certified Kubernetes Administrator"
            ],
            "nice_to_have": [
                "Scrum Master",
                "TOGAF",
                "ITIL"
            ],
            "weight": 5  # 5% of total score
        },
        
        "soft_skills": {
            "required": [
                "Teamwork",
                "Communication",
                "Problem solving",
                "Self-learning"
            ],
            "preferred": [
                "Leadership",
                "Mentoring",
                "Agile/Scrum experience",
                "English proficiency"
            ],
            "weight": 10  # 10% of total score
        },
        
        "scoring": {
            "min_pass_score": 60,
            "excellent_score": 80,
            "auto_reject_below": 40,
            "auto_interview_above": 85
        },
        
        "disqualifiers": [
            "Không có kinh nghiệm lập trình",
            "Không có học vấn liên quan và không có kinh nghiệm",
            "CV không đầy đủ thông tin"
        ]
    },
    
    "Frontend Developer": {
        "position_info": {
            "title": "Frontend Developer",
            "department": "Engineering",
            "level": "Junior-Mid",
            "salary_range": "12-25 triệu VND"
        },
        
        "technical_skills": {
            "required": {
                "core": ["HTML5", "CSS3", "JavaScript", "ES6+"],
                "frameworks": ["React", "Vue.js", "Angular"],
                "styling": ["Sass/SCSS", "Tailwind CSS", "Responsive Design"],
                "tools": ["Git", "Webpack", "npm/yarn"]
            },
            "preferred": {
                "advanced": ["TypeScript", "Next.js", "Nuxt.js"],
                "state": ["Redux", "Vuex", "MobX"],
                "testing": ["Jest", "React Testing Library", "Cypress"],
                "other": ["PWA", "Performance Optimization", "SEO"]
            },
            "weight": 50
        },
        
        "experience": {
            "min_years": 1,
            "max_years": 5,
            "preferred_years": 2,
            "industries": ["Web Development", "E-commerce", "SaaS"],
            "specific_experience": [
                "Building responsive web applications",
                "UI/UX implementation",
                "API integration",
                "Cross-browser compatibility"
            ],
            "weight": 25
        },
        
        "education": {
            "required_degree": "Bachelor",
            "preferred_majors": [
                "Computer Science",
                "Web Development",
                "Information Technology",
                "Design"
            ],
            "alternative_majors": [
                "Graphic Design",
                "Digital Media"
            ],
            "bootcamp_acceptable": True,
            "weight": 10
        },
        
        "certifications": {
            "preferred": [
                "Google Mobile Web Specialist",
                "React Developer Certification",
                "Front-End Web Developer (FreeCodeCamp)"
            ],
            "nice_to_have": [
                "Adobe Certified Expert",
                "UI/UX Design Certificate"
            ],
            "weight": 5
        },
        
        "soft_skills": {
            "required": [
                "Attention to detail",
                "Creativity",
                "Communication",
                "Teamwork"
            ],
            "preferred": [
                "UI/UX mindset",
                "Design thinking",
                "Agile methodology"
            ],
            "weight": 10
        },
        
        "scoring": {
            "min_pass_score": 55,
            "excellent_score": 80,
            "auto_reject_below": 35,
            "auto_interview_above": 85
        },
        
        "disqualifiers": [
            "Không biết HTML/CSS/JavaScript",
            "Không có portfolio hoặc demo projects",
            "Không có kinh nghiệm với framework nào"
        ]
    }
}

# ============================================
# CONFIGURATION MANAGER
# ============================================

class JobRequirementsManager:
    def __init__(self, config_file: str = "job_requirements_config.json"):
        self.config_file = Path(config_file)
        self.requirements = self.load_config()
    
    def load_config(self) -> Dict:
        """Load job requirements from config file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return DEFAULT_REQUIREMENTS.copy()
        return DEFAULT_REQUIREMENTS.copy()
    
    def save_config(self) -> bool:
        """Save job requirements to config file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.requirements, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_position_requirements(self, position: str) -> Dict:
        """Get requirements for a specific position"""
        return self.requirements.get(position, {})
    
    def add_position(self, position_name: str, requirements: Dict):
        """Add a new position with requirements"""
        self.requirements[position_name] = requirements
        return self.save_config()
    
    def update_position(self, position_name: str, requirements: Dict):
        """Update existing position requirements"""
        if position_name in self.requirements:
            self.requirements[position_name] = requirements
            return self.save_config()
        return False
    
    def delete_position(self, position_name: str):
        """Delete a position"""
        if position_name in self.requirements:
            del self.requirements[position_name]
            return self.save_config()
        return False
    
    def list_positions(self):
        """List all positions"""
        return list(self.requirements.keys())
    
    def export_to_excel(self, filename: str = "job_requirements.xlsx"):
        """Export all requirements to Excel for review"""
        import pandas as pd
        
        data = []
        for position, req in self.requirements.items():
            info = req.get('position_info', {})
            scoring = req.get('scoring', {})
            
            data.append({
                'Position': position,
                'Department': info.get('department', ''),
                'Level': info.get('level', ''),
                'Salary Range': info.get('salary_range', ''),
                'Min Experience': req.get('experience', {}).get('min_years', 0),
                'Min Pass Score': scoring.get('min_pass_score', 60),
                'Auto Interview Score': scoring.get('auto_interview_above', 85)
            })
        
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        return filename

# ============================================
# STREAMLIT UI FOR HR
# ============================================

def show_requirements_manager():
    """Streamlit UI for managing job requirements"""
    
    st.markdown("##  Quản Lý Yêu Cầu Tuyển Dụng")
    
    manager = JobRequirementsManager()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([" Xem Yêu Cầu", " Thêm/Sửa Vị Trí", " Export"])
    
    # TAB 1: View Requirements
    with tab1:
        st.markdown("###  Danh Sách Vị Trí")
        
        positions = manager.list_positions()
        
        if not positions:
            st.warning("Chưa có vị trí nào")
        else:
            selected_position = st.selectbox("Chọn vị trí:", positions)
            
            if selected_position:
                req = manager.get_position_requirements(selected_position)
                
                # Position Info
                st.markdown("####  Thông Tin Chung")
                info = req.get('position_info', {})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Department:** {info.get('department', 'N/A')}")
                    st.info(f"**Level:** {info.get('level', 'N/A')}")
                with col2:
                    st.info(f"**Salary:** {info.get('salary_range', 'N/A')}")
                
                st.markdown("---")
                
                # Technical Skills
                st.markdown("####  Technical Skills")
                tech = req.get('technical_skills', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Required:**")
                    required = tech.get('required', {})
                    for category, skills in required.items():
                        st.write(f"• {category.title()}: {', '.join(skills)}")
                
                with col2:
                    st.markdown("**Preferred:**")
                    preferred = tech.get('preferred', {})
                    for category, skills in preferred.items():
                        st.write(f"• {category.title()}: {', '.join(skills)}")
                
                st.caption(f"Weight: {tech.get('weight', 0)}% of total score")
                
                st.markdown("---")
                
                # Experience
                st.markdown("####  Experience Requirements")
                exp = req.get('experience', {})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Min Years", exp.get('min_years', 0))
                    st.metric("Preferred Years", exp.get('preferred_years', 0))
                
                with col2:
                    st.markdown("**Specific Experience:**")
                    for item in exp.get('specific_experience', []):
                        st.write(f"• {item}")
                
                st.caption(f"Weight: {exp.get('weight', 0)}% of total score")
                
                st.markdown("---")
                
                # Education
                st.markdown("####  Education Requirements")
                edu = req.get('education', {})
                
                st.write(f"**Required Degree:** {edu.get('required_degree', 'N/A')}")
                st.write(f"**Preferred Majors:** {', '.join(edu.get('preferred_majors', []))}")
                st.write(f"**Bootcamp Acceptable:** {' Yes' if edu.get('bootcamp_acceptable') else ' No'}")
                st.caption(f"Weight: {edu.get('weight', 0)}% of total score")
                
                st.markdown("---")
                
                # Scoring
                st.markdown("####  Scoring Thresholds")
                scoring = req.get('scoring', {})
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Min Pass", scoring.get('min_pass_score', 60))
                with col2:
                    st.metric("Excellent", scoring.get('excellent_score', 80))
                with col3:
                    st.metric("Auto Reject", f"< {scoring.get('auto_reject_below', 40)}")
                with col4:
                    st.metric("Auto Interview", f"> {scoring.get('auto_interview_above', 85)}")
                
                st.markdown("---")
                
                # Disqualifiers
                st.markdown("####  Disqualifiers")
                disqualifiers = req.get('disqualifiers', [])
                for item in disqualifiers:
                    st.error(f"• {item}")
    
    # TAB 2: Add/Edit Position
    with tab2:
        st.markdown("###  Thêm/Sửa Vị Trí Tuyển Dụng")
        
        mode = st.radio("Mode:", ["Tạo mới", "Chỉnh sửa"])
        
        if mode == "Chỉnh sửa":
            positions = manager.list_positions()
            edit_position = st.selectbox("Chọn vị trí cần sửa:", positions)
            base_req = manager.get_position_requirements(edit_position)
        else:
            edit_position = None
            base_req = {}
        
        with st.form("position_form"):
            st.markdown("####  Thông Tin Chung")
            
            col1, col2 = st.columns(2)
            
            with col1:
                position_name = st.text_input(
                    "Tên vị trí *",
                    value=edit_position if edit_position else "",
                    placeholder="e.g., DevOps Engineer"
                )
                
                department = st.text_input(
                    "Phòng ban",
                    value=base_req.get('position_info', {}).get('department', ''),
                    placeholder="e.g., Engineering"
                )
            
            with col2:
                level_options = ["Intern", "Junior", "Mid", "Mid-Senior", "Senior", "Lead", "Manager"]
                current_level = base_req.get('position_info', {}).get('level', 'Mid')
                
                # Find index safely
                try:
                    level_index = level_options.index(current_level)
                except ValueError:
                    level_index = 2  # Default to 'Mid'
                
                level = st.selectbox(
                    "Level",
                    level_options,
                    index=level_index
                )
                
                salary = st.text_input(
                    "Salary Range",
                    value=base_req.get('position_info', {}).get('salary_range', ''),
                    placeholder="e.g., 15-30 triệu VND"
                )
            
            st.markdown("---")
            st.markdown("####  Technical Skills (nhập mỗi skill 1 dòng)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                required_skills = st.text_area(
                    "Required Skills *",
                    value='\n'.join(
                        [skill for skills in base_req.get('technical_skills', {}).get('required', {}).values() for skill in skills]
                    ) if base_req else "",
                    height=150,
                    placeholder="Python\nJavaScript\nSQL\nGit"
                )
            
            with col2:
                preferred_skills = st.text_area(
                    "Preferred Skills",
                    value='\n'.join(
                        [skill for skills in base_req.get('technical_skills', {}).get('preferred', {}).values() for skill in skills]
                    ) if base_req else "",
                    height=150,
                    placeholder="Docker\nKubernetes\nAWS"
                )
            
            st.markdown("---")
            st.markdown("####  Experience")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_years = st.number_input(
                    "Min Years *",
                    min_value=0,
                    max_value=20,
                    value=base_req.get('experience', {}).get('min_years', 2)
                )
            
            with col2:
                pref_years = st.number_input(
                    "Preferred Years",
                    min_value=0,
                    max_value=20,
                    value=base_req.get('experience', {}).get('preferred_years', 3)
                )
            
            with col3:
                exp_weight = st.slider(
                    "Experience Weight %",
                    0, 50, 
                    base_req.get('experience', {}).get('weight', 25)
                )
            
            st.markdown("---")
            st.markdown("####  Scoring")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                min_pass = st.number_input(
                    "Min Pass Score",
                    0, 100,
                    base_req.get('scoring', {}).get('min_pass_score', 60)
                )
            
            with col2:
                excellent = st.number_input(
                    "Excellent Score",
                    0, 100,
                    base_req.get('scoring', {}).get('excellent_score', 80)
                )
            
            with col3:
                auto_reject = st.number_input(
                    "Auto Reject Below",
                    0, 100,
                    base_req.get('scoring', {}).get('auto_reject_below', 40)
                )
            
            with col4:
                auto_interview = st.number_input(
                    "Auto Interview Above",
                    0, 100,
                    base_req.get('scoring', {}).get('auto_interview_above', 85)
                )
            
            st.markdown("---")
            
            # Submit button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button(" Lưu Cấu Hình", use_container_width=True, type="primary")
            
            if submitted:
                if not position_name or not required_skills:
                    st.error(" Vui lòng điền đầy đủ thông tin bắt buộc!")
                else:
                    # Build requirements dict
                    new_req = {
                        "position_info": {
                            "title": position_name,
                            "department": department,
                            "level": level,
                            "salary_range": salary
                        },
                        "technical_skills": {
                            "required": {"skills": [s.strip() for s in required_skills.split('\n') if s.strip()]},
                            "preferred": {"skills": [s.strip() for s in preferred_skills.split('\n') if s.strip()]},
                            "weight": 50
                        },
                        "experience": {
                            "min_years": min_years,
                            "preferred_years": pref_years,
                            "weight": exp_weight
                        },
                        "scoring": {
                            "min_pass_score": min_pass,
                            "excellent_score": excellent,
                            "auto_reject_below": auto_reject,
                            "auto_interview_above": auto_interview
                        }
                    }
                    
                    if mode == "Tạo mới":
                        manager.add_position(position_name, new_req)
                        st.success(f" Đã tạo vị trí: {position_name}")
                    else:
                        manager.update_position(position_name, new_req)
                        st.success(f" Đã cập nhật vị trí: {position_name}")
                    
                    st.rerun()
    
    # TAB 3: Export
    with tab3:
        st.markdown("###  Export Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(" Export to JSON", use_container_width=True):
                manager.save_config()
                st.success(" Exported to job_requirements_config.json")
        
        with col2:
            if st.button(" Export to Excel", use_container_width=True):
                filename = manager.export_to_excel()
                st.success(f" Exported to {filename}")

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    st.set_page_config(page_title="Job Requirements Manager", layout="wide")
    show_requirements_manager()