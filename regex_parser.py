import os
import re
import pdfplumber
from docx2txt import process

class RegexResumeParser:
    """Regex-based resume parser - extracted from app.py for web app use"""
    
    def __init__(self):
        pass
    
    def extract_text_from_file(self, file_path):
        """Extract text from PDF or DOCX file"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Only PDF and DOCX are supported.")

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF using pdfplumber"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")

    def extract_text_from_docx(self, docx_path):
        """Extract text from DOCX using docx2txt"""
        try:
            text = process(docx_path)
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX: {e}")

    def extract_name(self, text):
        """Extract name from resume text"""
        lines = text.split('\n')
        # Usually name is in the first few lines
        for line in lines[:5]:
            line = line.strip()
            if line and len(line.split()) <= 4 and not '@' in line and not any(char.isdigit() for char in line):
                return line
        return None

    def extract_email(self, text):
        """Extract email using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None

    def extract_phone(self, text):
        """Extract phone number using regex"""
        phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        phones = re.findall(phone_pattern, text)
        return phones[0] if phones else None

    def extract_skills(self, text):
        """Extract skills section"""
        skills_keywords = ['skills', 'technical skills', 'technologies', 'programming languages']
        lines = text.split('\n')
        skills_section = []
        capture = False
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in skills_keywords):
                capture = True
                continue
            elif capture and (line_lower.startswith(('experience', 'education', 'projects', 'work history'))):
                break
            elif capture and line.strip():
                skills_section.append(line.strip())
        
        return skills_section[:5] if skills_section else None

    def extract_education(self, text):
        """Extract education information"""
        education_keywords = ['education', 'academic', 'university', 'college', 'degree']
        lines = text.split('\n')
        education_section = []
        capture = False
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in education_keywords):
                capture = True
                continue
            elif capture and (line_lower.startswith(('experience', 'skills', 'projects', 'work history'))):
                break
            elif capture and line.strip():
                education_section.append(line.strip())
        
        return education_section[:3] if education_section else None

    def extract_experience(self, text):
        """Extract work experience"""
        experience_keywords = ['experience', 'work history', 'employment', 'professional experience']
        lines = text.split('\n')
        experience_section = []
        capture = False
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in experience_keywords):
                capture = True
                continue
            elif capture and (line_lower.startswith(('education', 'skills', 'projects'))):
                break
            elif capture and line.strip():
                experience_section.append(line.strip())
        
        return experience_section[:5] if experience_section else None

    def extract_resume_data(self, resume_path):
        """Extract structured data from resume PDF or DOCX"""
        try:
            # Extract text from file (PDF or DOCX)
            text = self.extract_text_from_file(resume_path)
            
            if not text or not text.strip():
                raise Exception("No text content found in the file")
            
            # Parse the extracted text
            data = {
                'name': self.extract_name(text),
                'email': self.extract_email(text), 
                'mobile_number': self.extract_phone(text),
                'skills': self.extract_skills(text),
                'education': self.extract_education(text),
                'experience': self.extract_experience(text),
                'no_of_pages': len(text) // 3000 + 1,  # Rough estimate
            }
            
            return data
            
        except Exception as e:
            raise Exception(f"Error extracting resume data: {e}")