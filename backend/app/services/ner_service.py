import spacy
from typing import Dict, Any
import re
from datetime import datetime

class NERService:
    def __init__(self):
        try:
            # Try to load spaCy model, fallback to basic if not available
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model not found, use basic English model
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                # Fallback: will use regex-based extraction
                self.nlp = None
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities: Name, DOB, Address, ID Number"""
        entities = {
            "name": None,
            "dob": None,
            "address": None,
            "id_number": None
        }
        
        if not text:
            return entities
        
        # Use spaCy if available
        if self.nlp:
            doc = self.nlp(text)
            
            # Extract names (PERSON entities)
            names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
            if names:
                entities["name"] = names[0]  # Take first name found
            
            # Extract dates (DATE entities)
            dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
            for date_str in dates:
                dob = self._parse_date(date_str)
                if dob:
                    entities["dob"] = dob
                    break
        else:
            # Fallback regex-based extraction
            entities["name"] = self._extract_name_regex(text)
            entities["dob"] = self._extract_dob_regex(text)
        
        # Extract address (common patterns)
        entities["address"] = self._extract_address(text)
        
        # Extract ID number (alphanumeric patterns)
        entities["id_number"] = self._extract_id_number(text)
        
        return entities
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date string to standard format"""
        # Common date formats
        patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD
            r'\d{1,2}\s+\w+\s+\d{4}',        # DD Month YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                return match.group(0)
        return None
    
    def _extract_name_regex(self, text: str) -> str:
        """Extract name using regex patterns"""
        # Look for patterns like "Name:", "Full Name:", etc.
        patterns = [
            r'(?:Name|Full Name|FullName)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Simple two-word capitalized name
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_dob_regex(self, text: str) -> str:
        """Extract date of birth using regex"""
        patterns = [
            r'(?:DOB|Date of Birth|Birth Date)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',  # Any date pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None
    
    def _extract_address(self, text: str) -> str:
        """Extract address"""
        # Look for address patterns
        patterns = [
            r'(?:Address|Addr)[:\s]+([0-9]+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd|Court|Ct)[A-Za-z0-9\s,]+)',
            r'[0-9]+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd)',  # Simple street address
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None
    
    def _extract_id_number(self, text: str) -> str:
        """Extract ID number (passport, SSN, etc.)"""
        patterns = [
            r'(?:ID|ID Number|Passport|SSN|Social Security)[:\s#]+([A-Z0-9]{6,20})',
            r'[A-Z]{1,2}\d{6,12}',  # Alphanumeric ID patterns
            r'\d{3}-\d{2}-\d{4}',   # SSN format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None

