from openai import OpenAI
from typing import Dict, Any, List
from app.core.config import settings
from app.models.kyc import Document

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    def validate_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """Validate documents using LLM for cross-document consistency"""
        if not self.client:
            return {
                "validated": False,
                "reasoning": "OpenAI API key not configured",
                "fraud_signals": [],
                "mismatches": []
            }
        
        # Prepare document data for LLM
        document_data = []
        for doc in documents:
            doc_info = {
                "type": doc.document_type,
                "entities": doc.extracted_entities or {},
                "ocr_text": doc.ocr_text or "",
                "confidence": doc.ocr_confidence or 0.0
            }
            document_data.append(doc_info)
        
        # Create prompt for validation
        prompt = self._create_validation_prompt(document_data)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a KYC document validation expert. Analyze documents for consistency and fraud signals."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content
            
            # Parse LLM response (simplified - in production, use structured output)
            return self._parse_validation_response(result_text, document_data)
        except Exception as e:
            print(f"LLM Validation Error: {e}")
            return {
                "validated": False,
                "reasoning": f"Validation error: {str(e)}",
                "fraud_signals": [],
                "mismatches": []
            }
    
    def _create_validation_prompt(self, document_data: List[Dict]) -> str:
        """Create prompt for LLM validation"""
        prompt = """Analyze the following KYC documents for consistency and potential fraud signals.

Documents:
"""
        for i, doc in enumerate(document_data, 1):
            prompt += f"""
Document {i} - Type: {doc['type']}
Extracted Entities:
- Name: {doc['entities'].get('name', 'Not found')}
- DOB: {doc['entities'].get('dob', 'Not found')}
- Address: {doc['entities'].get('address', 'Not found')}
- ID Number: {doc['entities'].get('id_number', 'Not found')}
OCR Confidence: {doc['confidence']:.2f}

"""
        
        prompt += """
Please analyze:
1. Name consistency across documents
2. DOB consistency across documents
3. Address consistency across documents
4. ID number validity and consistency
5. Any suspicious patterns or fraud signals

Respond in JSON format:
{
    "validated": true/false,
    "reasoning": "explanation",
    "fraud_signals": ["signal1", "signal2"],
    "mismatches": {
        "name": "description if mismatch",
        "dob": "description if mismatch",
        "address": "description if mismatch"
    }
}
"""
        return prompt
    
    def _parse_validation_response(self, response_text: str, document_data: List[Dict]) -> Dict[str, Any]:
        """Parse LLM response (simplified parsing)"""
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                return parsed
            except:
                pass
        
        # Fallback: basic parsing
        validated = "validated" in response_text.lower() and "true" in response_text.lower()
        fraud_signals = []
        mismatches = {}
        
        # Simple keyword detection
        if "name mismatch" in response_text.lower():
            mismatches["name"] = "Name mismatch detected"
        if "dob mismatch" in response_text.lower() or "date mismatch" in response_text.lower():
            mismatches["dob"] = "DOB mismatch detected"
        if "address mismatch" in response_text.lower():
            mismatches["address"] = "Address mismatch detected"
        
        if "suspicious" in response_text.lower() or "fraud" in response_text.lower():
            fraud_signals.append("Suspicious patterns detected")
        
        return {
            "validated": validated,
            "reasoning": response_text[:500],  # First 500 chars
            "fraud_signals": fraud_signals,
            "mismatches": mismatches
        }

