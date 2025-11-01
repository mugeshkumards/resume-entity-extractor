import spacy
import re
import subprocess
import sys
import nltk
from datetime import datetime
from collections import defaultdict

class ResumeParser:
    def __init__(self):
        """Initialize NER models and patterns"""
        # Download and load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except (OSError, IOError):
            # Model not found, download it
            try:
                # Use spacy's CLI module for downloading (works on Streamlit Cloud)
                import spacy.cli
                spacy.cli.download("en_core_web_sm", quiet=True)
                self.nlp = spacy.load("en_core_web_sm")
            except Exception:
                # Fallback to subprocess method
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "spacy", "download", "en_core_web_sm"
                    ], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                    self.nlp = spacy.load("en_core_web_sm")
                except Exception:
                    # If all else fails, raise the error
                    raise RuntimeError(
                        "Failed to download spaCy model 'en_core_web_sm'. "
                        "Please ensure you have internet connection and try again."
                    )
        
        # Download NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            try:
                nltk.download('punkt', quiet=True)
            except Exception:
                # Continue even if download fails
                pass
        
        # Regex patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
        self.url_pattern = r'(https?://[^\s]+)|(www\.[^\s]+)|([a-zA-Z0-9]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)'
        
        # Skill keywords
        self.skill_keywords = {
            'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'express',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'nosql',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins',
            'git', 'agile', 'scrum', 'jira', 'ci/cd', 'devops', 'microservices',
            'machine learning', 'deep learning', 'ai', 'nlp', 'computer vision',
            'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn',
            'html', 'css', 'typescript', 'rest api', 'graphql', 'kafka', 'spark'
        }
        
        # Education keywords
        self.education_keywords = {
            'bachelor', 'master', 'phd', 'b.tech', 'm.tech', 'b.sc', 'm.sc',
            'b.e', 'm.e', 'mba', 'degree', 'diploma', 'certification'
        }
    
    def extract_entities(self, text):
        """Extract all entities from resume text"""
        doc = self.nlp(text)
        
        entities = {
            'name': self.extract_name(doc, text),
            'email': self.extract_email(text),
            'phone': self.extract_phone(text),
            'links': self.extract_links(text),
            'skills': self.extract_skills(text),
            'education': self.extract_education(text),
            'experience': self.extract_experience(text),
            'total_experience': self.calculate_experience(text),
            'highest_education': self.get_highest_education(text)
        }
        
        return entities
    
    def extract_name(self, doc, text):
        """Extract person name from resume"""
        # Method 1: Look for PERSON entity in first few lines
        lines = text.split('\n')[:5]
        first_text = ' '.join(lines)
        first_doc = self.nlp(first_text)
        
        for ent in first_doc.ents:
            if ent.label_ == 'PERSON':
                return ent.text
        
        # Method 2: First non-empty line is often the name
        for line in lines:
            line = line.strip()
            if line and len(line.split()) <= 4 and not any(char.isdigit() for char in line):
                return line
        
        return "Not found"
    
    def extract_email(self, text):
        """Extract email address"""
        emails = re.findall(self.email_pattern, text)
        return emails[0] if emails else "Not found"
    
    def extract_phone(self, text):
        """Extract phone number"""
        phones = re.findall(self.phone_pattern, text)
        # Filter out dates and other numbers
        valid_phones = [p for p in phones if len(re.sub(r'[^0-9]', '', p)) >= 10]
        return valid_phones[0] if valid_phones else "Not found"
    
    def extract_links(self, text):
        """Extract URLs (LinkedIn, GitHub, portfolio)"""
        links = re.findall(self.url_pattern, text, re.IGNORECASE)
        # Flatten and clean
        all_links = []
        for link_tuple in links:
            for link in link_tuple:
                if link:
                    all_links.append(link)
        return list(set(all_links))
    
    def extract_skills(self, text):
        """Extract technical skills"""
        text_lower = text.lower()
        found_skills = set()
        
        # Direct keyword matching
        for skill in self.skill_keywords:
            if skill in text_lower:
                found_skills.add(skill.title())
        
        # Look for skills section
        skills_section = re.search(
            r'skills[:\s]+(.*?)(?=\n\n|experience|education|$)', 
            text_lower, 
            re.DOTALL | re.IGNORECASE
        )
        
        if skills_section:
            skills_text = skills_section.group(1)
            # Extract items after bullets or commas
            skill_items = re.split(r'[,•\-\n]', skills_text)
            for item in skill_items:
                item = item.strip()
                if item and 2 < len(item) < 30:
                    found_skills.add(item.title())
        
        return sorted(list(found_skills))
    
    def extract_education(self, text):
        """Extract education details"""
        education_list = []
        
        # Find education section
        edu_section = re.search(
            r'education[:\s]+(.*?)(?=experience|skills|certifications|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if edu_section:
            edu_text = edu_section.group(1)
            lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
            
            current_edu = {}
            for line in lines:
                line_lower = line.lower()
                
                # Check for degree keywords
                if any(kw in line_lower for kw in self.education_keywords):
                    if current_edu:
                        education_list.append(current_edu)
                    current_edu = {'degree': line, 'institution': '', 'year': ''}
                
                # Extract year
                year_match = re.search(r'\b(19|20)\d{2}\b', line)
                if year_match and current_edu:
                    current_edu['year'] = year_match.group()
                
                # Institution name
                if current_edu and not current_edu['institution']:
                    if not any(kw in line_lower for kw in self.education_keywords):
                        current_edu['institution'] = line
            
            if current_edu:
                education_list.append(current_edu)
        
        return education_list
    
    def extract_experience(self, text):
        """Extract work experience"""
        experience_list = []
        
        # Find experience section
        exp_section = re.search(
            r'experience[:\s]+(.*?)(?=education|skills|certifications|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if exp_section:
            exp_text = exp_section.group(1)
            
            # Split by job entries (usually separated by blank lines)
            job_blocks = re.split(r'\n\n+', exp_text)
            
            for block in job_blocks:
                if not block.strip():
                    continue
                
                lines = [l.strip() for l in block.split('\n') if l.strip()]
                if not lines:
                    continue
                
                # First line is usually title | company
                title_line = lines[0]
                parts = re.split(r'\||@|at', title_line, flags=re.IGNORECASE)
                
                title = parts[0].strip() if len(parts) > 0 else ''
                company = parts[1].strip() if len(parts) > 1 else ''
                
                # Extract date range
                date_match = re.search(r'(\d{4})\s*-\s*(\d{4}|present)', block, re.IGNORECASE)
                duration = date_match.group() if date_match else ''
                
                # Description is rest of the lines
                description = '\n'.join(lines[1:])
                
                experience_list.append({
                    'title': title,
                    'company': company,
                    'duration': duration,
                    'description': description
                })
        
        return experience_list
    
    def calculate_experience(self, text):
        """Calculate total years of experience"""
        # Find all year ranges
        year_ranges = re.findall(r'(\d{4})\s*-\s*(\d{4}|present)', text, re.IGNORECASE)
        
        if not year_ranges:
            return "N/A"
        
        total_years = 0
        current_year = datetime.now().year
        
        for start, end in year_ranges:
            start_year = int(start)
            end_year = current_year if 'present' in end.lower() else int(end)
            total_years += (end_year - start_year)
        
        return f"{total_years} years"
    
    def get_highest_education(self, text):
        """Determine highest education level"""
        text_lower = text.lower()
        
        if 'phd' in text_lower or 'ph.d' in text_lower or 'doctorate' in text_lower:
            return "PhD"
        elif 'master' in text_lower or 'm.tech' in text_lower or 'm.sc' in text_lower or 'mba' in text_lower:
            return "Master's Degree"
        elif 'bachelor' in text_lower or 'b.tech' in text_lower or 'b.sc' in text_lower or 'b.e' in text_lower:
            return "Bachelor's Degree"
        elif 'diploma' in text_lower:
            return "Diploma"
        
        return "Not specified"