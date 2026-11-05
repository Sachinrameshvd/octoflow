import pypdf
from io import BytesIO
import re

class ResumeParser:
    def __init__(self, pdf_data):
        self.pdf_data = pdf_data
        self.document = pypdf.PdfReader(BytesIO(pdf_data))

    def extract_contact_info(self):
        contact_info = {}
        for page in self.document.pages:
            text = page.extract_text()
            if 'Email:' in text:
                email_match = re.search(r'Email: ([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
                if email_match:
                    contact_info['Email'] = email_match.group(1)
            if 'Phone:' in text:
                phone_match = re.search(r'Phone: (\d{3}-\d{3}-\d{4})', text)
                if phone_match:
                    contact_info['Phone'] = phone_match.group(1)
            if 'Address:' in text:
                address_match = re.search(r'Address: ([a-zA-Z0-9., ]+)', text)
                if address_match:
                    contact_info['Address'] = address_match.group(1)
        return contact_info

    def extract_sections(self):
        sections = {}
        for page in self.document.pages:
            text = page.extract_text()
            if 'Objective:' in text:
                objective_start = text.index('Objective:')
                objective_end = text.index('Education:')
                sections['Objective'] = text[objective_start:objective_end].strip()
            if 'Education:' in text:
                education_start = text.index('Education:')
                education_end = text.index('Experience:')
                sections['Education'] = text[education_start:education_end].strip()
            if 'Experience:' in text:
                experience_start = text.index('Experience:')
                experience_end = text.index('Skills:')
                sections['Experience'] = text[experience_start:experience_end].strip()
            if 'Skills:' in text:
                skills_start = text.index('Skills:')
                skills_end = text.index('References:')
                sections['Skills'] = text[skills_start:skills_end].strip()
            if 'References:' in text:
                references_start = text.index('References:')
                references_end = len(text)
                sections['References'] = text[references_start:references_end].strip()
        return sections

    def parse_resume(self):
        contact_info = self.extract_contact_info()
        sections = self.extract_sections()
        return {'contact_info': contact_info, 'sections': sections}