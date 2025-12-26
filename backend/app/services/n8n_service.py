import httpx
from typing import Dict, Any
from app.core.config import settings
from app.models.kyc import RiskScore

class N8NService:
    def __init__(self):
        self.webhook_url = settings.N8N_WEBHOOK_URL
        self.api_key = settings.N8N_API_KEY
    
    def trigger_workflow(self, application_id: int, risk_score: RiskScore):
        """Trigger n8n workflow for KYC processing"""
        if not self.webhook_url:
            print("N8N webhook URL not configured")
            return
        
        payload = {
            "application_id": application_id,
            "risk_score": risk_score.score,
            "decision": risk_score.decision,
            "reasoning": risk_score.reasoning,
            "risk_factors": risk_score.risk_factors
        }
        
        try:
            headers = {}
            if self.api_key:
                headers["X-N8N-API-KEY"] = self.api_key
            
            response = httpx.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            print(f"N8N workflow triggered for application {application_id}")
        except Exception as e:
            print(f"Error triggering N8N workflow: {e}")
            # Don't fail the request if n8n is unavailable

