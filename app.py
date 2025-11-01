import streamlit as st
import pandas as pd
import plotly.express as px
from models.resume_parser import ResumeParser
from utils.pdf_handler import extract_text_from_pdf, extract_text_from_docx
import json

# Page configuration
st.set_page_config(
    page_title="Resume Entity Extractor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .entity-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .skill-badge {
        display: inline-block;
        background: #4CAF50;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        margin: 0.2rem;
        font-size: 0.9rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/resume.png", width=150)
    st.title("📄 Resume Analyzer")
    st.markdown("---")
    
    option = st.radio(
        "Choose Input Method:",
        ["Upload Resume", "Paste Text", "Try Sample"]
    )
    
    st.markdown("---")
    st.markdown("### 🎯 Extracted Entities")
    st.markdown("""
    - 👤 Name
    - 📧 Email
    - 📱 Phone
    - 💼 Skills
    - 🎓 Education
    - 💻 Experience
    - 🔗 Links (LinkedIn, GitHub)
    """)

# Main content
st.markdown('<h1 class="main-header">🤖 AI-Powered Resume Entity Extractor</h1>', 
            unsafe_allow_html=True)

# Initialize parser with error handling
@st.cache_resource
def load_parser():
    try:
        return ResumeParser()
    except Exception as e:
        st.error(f"Error initializing parser: {str(e)}")
        st.info("Please check the logs or try refreshing the page.")
        return None

parser = load_parser()

if parser is None:
    st.stop()

# Input handling
resume_text = ""

if option == "Upload Resume":
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF, DOCX, or TXT)", 
        type=['pdf', 'docx', 'txt']
    )
    
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            resume_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            resume_text = extract_text_from_docx(uploaded_file)
        else:
            resume_text = uploaded_file.read().decode('utf-8')

elif option == "Paste Text":
    resume_text = st.text_area(
        "Paste your resume text here:", 
        height=300,
        placeholder="Enter resume text..."
    )

elif option == "Try Sample":
    resume_text = """John Doe
Senior Software Engineer

Contact:
Email: john.doe@email.com
Phone: +1-555-123-4567
LinkedIn: linkedin.com/in/johndoe
GitHub: github.com/johndoe

Summary:
Experienced software engineer with 5+ years in full-stack development, 
specializing in Python, JavaScript, and cloud technologies.

Skills:
- Programming: Python, JavaScript, Java, C++
- Web: React, Node.js, Django, Flask
- Database: PostgreSQL, MongoDB, Redis
- Cloud: AWS, Docker, Kubernetes
- Tools: Git, Jenkins, Terraform

Experience:

Senior Software Engineer | Tech Corp | 2021 - Present
- Led development of microservices architecture serving 1M+ users
- Implemented CI/CD pipeline reducing deployment time by 60%
- Mentored team of 5 junior developers

Software Engineer | StartupXYZ | 2019 - 2021
- Built RESTful APIs using Python and Django
- Optimized database queries improving performance by 40%

Education:

Master of Science in Computer Science
Stanford University | 2017 - 2019

Bachelor of Technology in Computer Engineering  
MIT | 2013 - 2017

Certifications:
- AWS Solutions Architect - Professional
- Certified Kubernetes Administrator (CKA)
"""
    st.info("📝 Sample resume loaded. Click 'Extract Entities' to analyze.")

# Extract button
if st.button("🚀 Extract Entities", use_container_width=True):
    if resume_text:
        if parser is None:
            st.error("❌ Parser not initialized. Please refresh the page.")
        else:
            try:
                with st.spinner("🔍 Analyzing resume..."):
                    extracted_data = parser.extract_entities(resume_text)
                    st.session_state.extracted_data = extracted_data
                    st.success("✅ Extraction completed!")
            except Exception as e:
                st.error(f"❌ Error during extraction: {str(e)}")
                st.info("Please try again or check your input.")
    else:
        st.warning("⚠️ Please provide resume text first.")

# Display results
if st.session_state.extracted_data:
    data = st.session_state.extracted_data
    
    st.markdown("---")
    st.markdown("## 📊 Extracted Information")
    
    # Create columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 👤 Personal Information")
        st.markdown(f"**Name:** {data.get('name', 'Not found')}")
        st.markdown(f"**Email:** {data.get('email', 'Not found')}")
        st.markdown(f"**Phone:** {data.get('phone', 'Not found')}")
        
        if data.get('links'):
            st.markdown("**Links:**")
            for link in data['links']:
                st.markdown(f"- {link}")
    
    with col2:
        st.markdown("### 💼 Professional Summary")
        st.markdown(f"**Total Experience:** {data.get('total_experience', 'N/A')}")
        st.markdown(f"**Highest Education:** {data.get('highest_education', 'N/A')}")
        st.markdown(f"**Skills Count:** {len(data.get('skills', []))}")
    
    # Skills visualization
    st.markdown("---")
    st.markdown("### 🎯 Skills")
    
    if data.get('skills'):
        skills_html = "".join([f'<span class="skill-badge">{skill}</span>' 
                               for skill in data['skills']])
        st.markdown(skills_html, unsafe_allow_html=True)
        
        # Skills categorization visualization
        if len(data['skills']) > 0:
            # Simple categorization (you can enhance this)
            skill_categories = {
                'Programming': [],
                'Web': [],
                'Database': [],
                'Cloud': [],
                'Other': []
            }
            
            for skill in data['skills']:
                skill_lower = skill.lower()
                if any(x in skill_lower for x in ['python', 'java', 'javascript', 'c++', 'c#']):
                    skill_categories['Programming'].append(skill)
                elif any(x in skill_lower for x in ['react', 'angular', 'vue', 'node', 'django', 'flask']):
                    skill_categories['Web'].append(skill)
                elif any(x in skill_lower for x in ['sql', 'mongodb', 'postgres', 'mysql', 'redis']):
                    skill_categories['Database'].append(skill)
                elif any(x in skill_lower for x in ['aws', 'azure', 'gcp', 'docker', 'kubernetes']):
                    skill_categories['Cloud'].append(skill)
                else:
                    skill_categories['Other'].append(skill)
            
            # Create dataframe for visualization
            category_counts = {k: len(v) for k, v in skill_categories.items() if len(v) > 0}
            if category_counts:
                df_skills = pd.DataFrame(
                    list(category_counts.items()), 
                    columns=['Category', 'Count']
                )
                fig = px.bar(df_skills, x='Category', y='Count', 
                            title='Skills by Category',
                            color='Count',
                            color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
    
    # Experience section
    st.markdown("---")
    st.markdown("### 💻 Work Experience")
    
    if data.get('experience'):
        for i, exp in enumerate(data['experience'], 1):
            with st.expander(f"**{exp.get('title', 'Position')}** at {exp.get('company', 'Company')}", 
                           expanded=(i==1)):
                st.markdown(f"**Duration:** {exp.get('duration', 'N/A')}")
                st.markdown(f"**Description:**")
                st.markdown(exp.get('description', 'No description available'))
    
    # Education section
    st.markdown("---")
    st.markdown("### 🎓 Education")
    
    if data.get('education'):
        for edu in data['education']:
            st.markdown(f"""
            **{edu.get('degree', 'Degree')}**  
            {edu.get('institution', 'Institution')} | {edu.get('year', 'Year')}
            """)
    
    # Export options
    st.markdown("---")
    st.markdown("### 💾 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        json_data = json.dumps(data, indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_data,
            file_name="resume_data.json",
            mime="application/json"
        )
    
    with col2:
        df = pd.DataFrame([{
            'Name': data.get('name', ''),
            'Email': data.get('email', ''),
            'Phone': data.get('phone', ''),
            'Skills': ', '.join(data.get('skills', [])),
            'Experience': data.get('total_experience', ''),
            'Education': data.get('highest_education', '')
        }])
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📊 Download CSV",
            data=csv_data,
            file_name="resume_data.csv",
            mime="text/csv"
        )
    
    with col3:
        # Create a formatted text report
        report = f"""RESUME ANALYSIS REPORT
{'='*50}

PERSONAL INFORMATION
Name: {data.get('name', 'Not found')}
Email: {data.get('email', 'Not found')}
Phone: {data.get('phone', 'Not found')}

SKILLS ({len(data.get('skills', []))})
{chr(10).join(['- ' + skill for skill in data.get('skills', [])])}

EXPERIENCE
Total Experience: {data.get('total_experience', 'N/A')}

EDUCATION
{data.get('highest_education', 'N/A')}
"""
        st.download_button(
            label="📝 Download Report",
            data=report,
            file_name="resume_report.txt",
            mime="text/plain"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Built with ❤️ using Streamlit | Powered by spaCy & Transformers</p>
</div>
""", unsafe_allow_html=True)