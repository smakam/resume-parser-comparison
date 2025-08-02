import os
import re
import sys
import pdfplumber
import spacy
from docx2txt import process

print("Resume Parser Initialized")

def extract_text_from_file(file_path):
    """Extract text from PDF or DOCX file"""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. Only PDF and DOCX are supported.")

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdfplumber"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        print("PDF content extracted successfully")
        return text
    except Exception as e:
        raise Exception(f"Error reading PDF: {e}")

def extract_text_from_docx(docx_path):
    """Extract text from DOCX using docx2txt"""
    try:
        text = process(docx_path)
        print("DOCX content extracted successfully")
        return text
    except Exception as e:
        raise Exception(f"Error reading DOCX: {e}")

def extract_resume_data(resume_path):
    """Extract structured data from resume PDF or DOCX"""
    try:
        # Extract text from file (PDF or DOCX)
        text = extract_text_from_file(resume_path)
        
        if not text or not text.strip():
            raise Exception("No text content found in the file")
        
        # Parse the extracted text
        data = {
            'name': extract_name(text),
            'email': extract_email(text), 
            'mobile_number': extract_phone(text),
            'skills': extract_skills(text),
            'education': extract_education(text),
            'experience': extract_experience(text)
        }
        
        return data
        
    except Exception as e:
        print(f"Error extracting resume data: {e}")
        return None

def extract_name(text):
    """Extract name from resume text"""
    lines = text.split('\n')
    # Usually name is in the first few lines
    for line in lines[:5]:
        line = line.strip()
        if line and len(line.split()) <= 4 and not '@' in line and not any(char.isdigit() for char in line):
            return line
    return "Not found"

def extract_email(text):
    """Extract email using regex"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else "Not found"

def extract_phone(text):
    """Extract phone number using regex"""
    phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
    phones = re.findall(phone_pattern, text)
    return phones[0] if phones else "Not found"

def extract_skills(text):
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
    
    return skills_section[:5] if skills_section else ["Not found"]

def extract_education(text):
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
    
    return education_section[:3] if education_section else ["Not found"]

def extract_experience(text):
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
    
    return experience_section[:5] if experience_section else ["Not found"]

# Find resume file - try multiple formats
def find_resume_file():
    """Find the first available resume file in supported formats"""
    resume_files = [
        'resume.pdf',
        'resume.docx', 
        'Level4_Software_Engineer_Resume.pdf',
        'Level4_Software_Engineer_Resume.docx',
        'Level4_Software_Engineer_Resume (1).docx'
    ]
    
    for filename in resume_files:
        file_path = os.path.join(os.getcwd(), filename)
        if os.path.exists(file_path):
            return file_path
    
    return None

def get_resume_file():
    """Get resume file path from command line argument or auto-discover"""
    if len(sys.argv) > 1:
        # File provided as command line argument
        resume_path = sys.argv[1]
        
        # Handle relative paths
        if not os.path.isabs(resume_path):
            resume_path = os.path.join(os.getcwd(), resume_path)
            
        if not os.path.exists(resume_path):
            print(f"Error: File '{sys.argv[1]}' not found.")
            sys.exit(1)
            
        # Check if file format is supported
        file_ext = os.path.splitext(resume_path)[1].lower()
        if file_ext not in ['.pdf', '.docx', '.doc']:
            print(f"Error: Unsupported file format '{file_ext}'.")
            print("Supported formats: .pdf, .docx, .doc")
            sys.exit(1)
            
        return resume_path
    else:
        # Auto-discover file in current directory
        resume_path = find_resume_file()
        if not resume_path:
            print("Usage: python app.py <resume_file>")
            print("   or: python app.py  (to auto-discover resume file)")
            print("")
            print("Supported formats: PDF (.pdf) and Word documents (.docx, .doc)")
            print("")
            print("Examples:")
            print("  python app.py resume.pdf")
            print("  python app.py my_resume.docx")
            print("  python app.py /path/to/resume.pdf")
            sys.exit(1)
        return resume_path

# Get resume file path
resume_path = get_resume_file()

print(f"Processing file: {os.path.basename(resume_path)}")

# Extract data using custom parser
data = extract_resume_data(resume_path)

# Print the extracted data
if data:
    print("\n" + "="*50)
    print("RESUME PARSING RESULTS")
    print("="*50)
    print(f"File: {os.path.basename(resume_path)}")
    print(f"Format: {os.path.splitext(resume_path)[1].upper()}")
    print("-"*50)
    print(f"Name: {data.get('name')}")
    print(f"Email: {data.get('email')}")
    print(f"Mobile Number: {data.get('mobile_number')}")
    print(f"Skills: {data.get('skills')}")
    print(f"Education: {data.get('education')}")
    print(f"Experience: {data.get('experience')}")
    print("="*50)
else:
    print("Could not parse the resume.")