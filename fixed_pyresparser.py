import os
import sys
import spacy
from spacy.matcher import Matcher
import re
import pdfplumber
from docx2txt import process
import pandas as pd

print("Fixed PyResParser with spaCy and NLTK")

class FixedResumeParser:
    """Fixed version of ResumeParser using modern spaCy and NLTK"""
    
    def __init__(self, resume_path, skills_file=None):
        # Load standard spaCy model instead of broken custom model
        self.nlp = spacy.load('en_core_web_sm')
        self.matcher = Matcher(self.nlp.vocab)
        self.resume_path = resume_path
        
        # Setup entity patterns for better extraction
        self._setup_patterns()
        
        # Load skills database if provided
        self.skills_db = self._load_skills_database(skills_file)
    
    def _setup_patterns(self):
        """Setup spaCy patterns for entity recognition"""
        
        # Email pattern
        email_pattern = [{"LIKE_EMAIL": True}]
        self.matcher.add("EMAIL", [email_pattern])
        
        # Phone patterns
        phone_patterns = [
            [{"SHAPE": "ddd-ddd-dddd"}],
            [{"SHAPE": "(ddd) ddd-dddd"}],
            [{"SHAPE": "ddd.ddd.dddd"}],
            [{"SHAPE": "ddd ddd dddd"}]
        ]
        self.matcher.add("PHONE", phone_patterns)
        
        # Degree patterns
        degree_patterns = [
            [{"LOWER": {"IN": ["bachelor", "master", "phd", "doctorate", "b.s.", "m.s.", "ph.d."]}},
             {"LOWER": "of", "OP": "?"},
             {"LOWER": {"IN": ["science", "arts", "engineering", "technology", "business"]}}],
            [{"LOWER": {"IN": ["bs", "ms", "phd", "ba", "ma"]}},
             {"LOWER": "in", "OP": "?"}]
        ]
        self.matcher.add("DEGREE", degree_patterns)
        
        # Skills patterns - common tech skills
        skill_patterns = [
            [{"LOWER": {"IN": ["python", "java", "javascript", "react", "angular", "node.js", "docker", "kubernetes"]}}],
            [{"LOWER": "machine"}, {"LOWER": "learning"}],
            [{"LOWER": "data"}, {"LOWER": "science"}],
            [{"LOWER": "artificial"}, {"LOWER": "intelligence"}]
        ]
        self.matcher.add("SKILL", skill_patterns)
    
    def _load_skills_database(self, skills_file):
        """Load skills database from CSV or use default"""
        if skills_file and os.path.exists(skills_file):
            try:
                df = pd.read_csv(skills_file)
                return df['skill'].str.lower().tolist() if 'skill' in df.columns else []
            except:
                pass
        
        # Default skills database
        return [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
            'django', 'flask', 'spring', 'express', 'docker', 'kubernetes',
            'aws', 'azure', 'gcp', 'mongodb', 'postgresql', 'mysql', 'redis',
            'machine learning', 'deep learning', 'data science', 'ai', 'ml',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
            'git', 'jenkins', 'ci/cd', 'agile', 'scrum', 'rest api', 'graphql'
        ]
    
    def _extract_text_from_file(self, file_path):
        """Extract text from PDF or DOCX"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
        elif file_ext in ['.docx', '.doc']:
            return process(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _extract_name_with_spacy(self, text):
        """Extract name using spaCy NER with improved logic"""
        # Strategy 1: Look for name patterns in first few lines
        lines = text.split('\n')
        for line in lines[:8]:  # Check first 8 lines
            line = line.strip()
            # Skip empty lines and obvious non-names
            if not line or '@' in line or 'phone' in line.lower() or 'email' in line.lower():
                continue
                
            # Check if line looks like a name (all caps, title case, or proper formatting)
            words = line.split()
            if (2 <= len(words) <= 4 and 
                not any(char.isdigit() for char in line) and
                not any(word.lower() in ['street', 'road', 'avenue', 'drive', 'lane', 'heritage', 'apartment', 'building'] for word in words)):
                
                # Prefer lines that are all caps or title case (typical resume formatting)
                if (line.isupper() or line.istitle() or 
                    all(word[0].isupper() for word in words if word.isalpha())):
                    return line
        
        # Strategy 2: Use spaCy NER but with better filtering
        doc = self.nlp(text[:2000])  # Process first 2000 chars
        person_entities = []
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name_text = ent.text.strip()
                words = name_text.split()
                
                # Filter out common false positives
                if (2 <= len(words) <= 4 and 
                    not any(word.lower() in ['heritage', 'society', 'apartment', 'building', 'street', 'road'] for word in words) and
                    not any(char.isdigit() for char in name_text)):
                    person_entities.append((name_text, ent.start_char))
        
        # Return the first valid person entity (usually closest to top)
        if person_entities:
            # Sort by position in text (earlier = better)
            person_entities.sort(key=lambda x: x[1])
            return person_entities[0][0]
        
        # Strategy 3: Fallback to simple first line that looks like a name
        for line in lines[:5]:
            line = line.strip()
            if (line and 2 <= len(line.split()) <= 4 and 
                not '@' in line and not any(char.isdigit() for char in line) and
                all(word[0].isupper() for word in line.split() if word.isalpha())):
                return line
        
        return None
    
    def _extract_email_with_spacy(self, text):
        """Extract email using spaCy patterns and regex"""
        doc = self.nlp(text)
        matches = self.matcher(doc)
        
        for match_id, start, end in matches:
            if self.nlp.vocab.strings[match_id] == "EMAIL":
                return doc[start:end].text
        
        # Fallback to regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None
    
    def _extract_phone_with_spacy(self, text):
        """Extract phone using spaCy patterns and regex"""
        doc = self.nlp(text)
        matches = self.matcher(doc)
        
        for match_id, start, end in matches:
            if self.nlp.vocab.strings[match_id] == "PHONE":
                return doc[start:end].text
        
        # Fallback to regex
        phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0]
        
        return None
    
    def _extract_education_with_spacy(self, text):
        """Extract education using spaCy NER and patterns"""
        doc = self.nlp(text)
        education = []
        
        # Look for educational institutions
        for ent in doc.ents:
            if ent.label_ in ["ORG"] and any(keyword in ent.text.lower() 
                for keyword in ["university", "college", "institute", "school"]):
                education.append(ent.text)
        
        # Look for degrees using matcher
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            if self.nlp.vocab.strings[match_id] == "DEGREE":
                education.append(doc[start:end].text)
        
        return list(set(education)) if education else None
    
    def _extract_skills_with_spacy(self, text):
        """Extract skills using spaCy and skills database"""
        doc = self.nlp(text)
        found_skills = []
        text_lower = text.lower()
        
        # Use skills database
        for skill in self.skills_db:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        # Use spaCy patterns
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            if self.nlp.vocab.strings[match_id] == "SKILL":
                found_skills.append(doc[start:end].text)
        
        # Extract technology mentions using NER
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "ORG"] and len(ent.text.split()) <= 2:
                # Could be a technology/framework
                if any(tech_word in ent.text.lower() for tech_word in 
                      ['js', 'sql', 'api', 'framework', 'library']):
                    found_skills.append(ent.text)
        
        return list(set(found_skills))[:10] if found_skills else None  # Limit to 10 skills
    
    def _extract_experience_with_spacy(self, text):
        """Extract work experience using spaCy NER"""
        doc = self.nlp(text)
        companies = []
        positions = []
        
        # Extract organizations (potential companies)
        for ent in doc.ents:
            if ent.label_ == "ORG":
                # Filter out universities and common non-company entities
                if not any(keyword in ent.text.lower() for keyword in 
                          ["university", "college", "school", "institute"]):
                    companies.append(ent.text)
        
        # Look for job titles in text
        job_title_keywords = [
            'engineer', 'developer', 'manager', 'analyst', 'consultant',
            'specialist', 'coordinator', 'director', 'lead', 'senior',
            'junior', 'intern', 'associate', 'architect', 'designer'
        ]
        
        sentences = [sent.text for sent in doc.sents]
        for sentence in sentences:
            if any(title in sentence.lower() for title in job_title_keywords):
                positions.append(sentence.strip())
                if len(positions) >= 3:  # Limit to 3 positions
                    break
        
        experience = {
            'companies': companies[:5] if companies else None,
            'positions': positions[:3] if positions else None
        }
        
        return experience
    
    def get_extracted_data(self):
        """Extract all data from resume using spaCy and NLTK"""
        try:
            # Extract text from file
            text = self._extract_text_from_file(self.resume_path)
            
            if not text or not text.strip():
                return None
            
            print("Text extracted successfully")
            
            # Use spaCy for advanced extraction
            extracted_data = {
                'name': self._extract_name_with_spacy(text),
                'email': self._extract_email_with_spacy(text),
                'mobile_number': self._extract_phone_with_spacy(text),
                'skills': self._extract_skills_with_spacy(text),
                'education': self._extract_education_with_spacy(text),
                'experience': self._extract_experience_with_spacy(text),
                'no_of_pages': len(text) // 3000 + 1,  # Rough estimate
            }
            
            # Add convenience fields
            if extracted_data['experience']:
                extracted_data['company_names'] = extracted_data['experience'].get('companies')
                extracted_data['designation'] = extracted_data['experience'].get('positions')
            
            # Calculate total experience (basic heuristic)
            experience_keywords = ['years', 'year', 'experience']
            exp_matches = []
            for keyword in experience_keywords:
                pattern = rf'(\d+)[\s\+]*{keyword}'
                matches = re.findall(pattern, text.lower())
                exp_matches.extend(matches)
            
            if exp_matches:
                extracted_data['total_experience'] = f"{max(exp_matches)}+ years"
            
            return extracted_data
            
        except Exception as e:
            print(f"Error extracting data: {e}")
            return None

def main():
    """Main function to test the fixed parser"""
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
        if not os.path.isabs(resume_path):
            resume_path = os.path.join(os.getcwd(), resume_path)
    else:
        # Auto-discover resume file
        resume_files = ['resume.pdf', 'resume.docx', 'Level4_Software_Engineer_Resume.pdf', 
                       'Level4_Software_Engineer_Resume.docx']
        resume_path = None
        for filename in resume_files:
            test_path = os.path.join(os.getcwd(), filename)
            if os.path.exists(test_path):
                resume_path = test_path
                break
        
        if not resume_path:
            print("Usage: python fixed_pyresparser.py <resume_file>")
            print("No resume file found for auto-discovery")
            return
    
    if not os.path.exists(resume_path):
        print(f"Error: File '{resume_path}' not found")
        return
    
    print(f"Processing: {os.path.basename(resume_path)}")
    
    # Create parser and extract data
    parser = FixedResumeParser(resume_path)
    data = parser.get_extracted_data()
    
    if data:
        print("\n" + "="*60)
        print("FIXED PYRESPARSER RESULTS (spaCy + NLTK)")
        print("="*60)
        
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 5:
                print(f"{key}: {value[:5]}... (showing first 5)")
            else:
                print(f"{key}: {value}")
        
        print("="*60)
    else:
        print("Failed to extract data from resume")

if __name__ == "__main__":
    main()