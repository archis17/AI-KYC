from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.kyc import KYCApplication, Document, RiskScore
from app.schemas.kyc import RiskScoreResponse

class RiskScoringService:
    # Risk factor weights
    WEIGHTS = {
        "name_mismatch": 25.0,
        "dob_mismatch": 20.0,
        "address_mismatch": 15.0,
        "low_ocr_confidence": 20.0,
        "missing_documents": 20.0,
        "fraud_signals": 30.0
    }
    
    # Thresholds
    APPROVED_THRESHOLD = 30.0
    REVIEW_THRESHOLD = 60.0
    
    def calculate_risk_score(self, application: KYCApplication, db: Session) -> RiskScore:
        """Calculate risk score for application"""
        documents = db.query(Document).filter(
            Document.application_id == application.id
        ).all()
        
        risk_factors = {}
        total_risk = 0.0
        
        # 1. Check name consistency
        name_mismatch_score = self._check_name_mismatch(documents)
        risk_factors["name_mismatch"] = {
            "score": name_mismatch_score,
            "weight": self.WEIGHTS["name_mismatch"],
            "contribution": name_mismatch_score * self.WEIGHTS["name_mismatch"] / 100
        }
        total_risk += risk_factors["name_mismatch"]["contribution"]
        
        # 2. Check DOB consistency
        dob_mismatch_score = self._check_dob_mismatch(documents)
        risk_factors["dob_mismatch"] = {
            "score": dob_mismatch_score,
            "weight": self.WEIGHTS["dob_mismatch"],
            "contribution": dob_mismatch_score * self.WEIGHTS["dob_mismatch"] / 100
        }
        total_risk += risk_factors["dob_mismatch"]["contribution"]
        
        # 3. Check address consistency
        address_mismatch_score = self._check_address_mismatch(documents)
        risk_factors["address_mismatch"] = {
            "score": address_mismatch_score,
            "weight": self.WEIGHTS["address_mismatch"],
            "contribution": address_mismatch_score * self.WEIGHTS["address_mismatch"] / 100
        }
        total_risk += risk_factors["address_mismatch"]["contribution"]
        
        # 4. Check OCR confidence
        ocr_confidence_score = self._check_ocr_confidence(documents)
        risk_factors["low_ocr_confidence"] = {
            "score": ocr_confidence_score,
            "weight": self.WEIGHTS["low_ocr_confidence"],
            "contribution": ocr_confidence_score * self.WEIGHTS["low_ocr_confidence"] / 100
        }
        total_risk += risk_factors["low_ocr_confidence"]["contribution"]
        
        # 5. Check missing documents
        missing_docs_score = self._check_missing_documents(documents)
        risk_factors["missing_documents"] = {
            "score": missing_docs_score,
            "weight": self.WEIGHTS["missing_documents"],
            "contribution": missing_docs_score * self.WEIGHTS["missing_documents"] / 100
        }
        total_risk += risk_factors["missing_documents"]["contribution"]
        
        # 6. Check fraud signals from LLM validation
        fraud_signals_score = self._check_fraud_signals(documents)
        risk_factors["fraud_signals"] = {
            "score": fraud_signals_score,
            "weight": self.WEIGHTS["fraud_signals"],
            "contribution": fraud_signals_score * self.WEIGHTS["fraud_signals"] / 100
        }
        total_risk += risk_factors["fraud_signals"]["contribution"]
        
        # Clamp score to 0-100
        final_score = min(100.0, max(0.0, total_risk))
        
        # Determine decision
        if final_score <= self.APPROVED_THRESHOLD:
            decision = "approved"
        elif final_score <= self.REVIEW_THRESHOLD:
            decision = "review"
        else:
            decision = "rejected"
        
        # Generate human-readable reasoning
        reasoning = self._generate_reasoning(final_score, risk_factors, decision)
        
        # Create or update risk score
        existing_score = db.query(RiskScore).filter(
            RiskScore.application_id == application.id
        ).first()
        
        if existing_score:
            existing_score.score = final_score
            existing_score.decision = decision
            existing_score.reasoning = reasoning
            existing_score.risk_factors = risk_factors
            db.commit()
            db.refresh(existing_score)
            return existing_score
        else:
            risk_score = RiskScore(
                application_id=application.id,
                score=final_score,
                decision=decision,
                reasoning=reasoning,
                risk_factors=risk_factors
            )
            db.add(risk_score)
            db.commit()
            db.refresh(risk_score)
            return risk_score
    
    def _check_name_mismatch(self, documents: List[Document]) -> float:
        """Check for name mismatches across documents (0-100)"""
        names = []
        for doc in documents:
            if doc.extracted_entities and doc.extracted_entities.get("name"):
                names.append(doc.extracted_entities["name"].lower().strip())
        
        if len(names) < 2:
            return 0.0  # Can't compare with less than 2 names
        
        # Check if all names are similar
        unique_names = set(names)
        if len(unique_names) == 1:
            return 0.0  # All names match
        
        # Calculate mismatch score based on similarity
        # Simple: if names don't match exactly, assign score based on number of unique names
        mismatch_ratio = (len(unique_names) - 1) / len(names)
        return min(100.0, mismatch_ratio * 100)
    
    def _check_dob_mismatch(self, documents: List[Document]) -> float:
        """Check for DOB mismatches (0-100)"""
        dobs = []
        for doc in documents:
            if doc.extracted_entities and doc.extracted_entities.get("dob"):
                dobs.append(doc.extracted_entities["dob"].strip())
        
        if len(dobs) < 2:
            return 0.0
        
        unique_dobs = set(dobs)
        if len(unique_dobs) == 1:
            return 0.0
        
        mismatch_ratio = (len(unique_dobs) - 1) / len(dobs)
        return min(100.0, mismatch_ratio * 100)
    
    def _check_address_mismatch(self, documents: List[Document]) -> float:
        """Check for address mismatches (0-100)"""
        addresses = []
        for doc in documents:
            if doc.extracted_entities and doc.extracted_entities.get("address"):
                addresses.append(doc.extracted_entities["address"].lower().strip())
        
        if len(addresses) < 2:
            return 0.0
        
        unique_addresses = set(addresses)
        if len(unique_addresses) == 1:
            return 0.0
        
        mismatch_ratio = (len(unique_addresses) - 1) / len(addresses)
        return min(100.0, mismatch_ratio * 100)
    
    def _check_ocr_confidence(self, documents: List[Document]) -> float:
        """Check OCR confidence (0-100, higher = more risk)"""
        if not documents:
            return 100.0
        
        confidences = [doc.ocr_confidence or 0.0 for doc in documents]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Convert confidence to risk (low confidence = high risk)
        # If avg confidence is 0.9, risk is 10 (100 - 90)
        return max(0.0, 100.0 - (avg_confidence * 100))
    
    def _check_missing_documents(self, documents: List[Document]) -> float:
        """Check for missing required documents (0-100)"""
        required_types = ["id_card", "passport", "proof_of_address"]
        document_types = [doc.document_type for doc in documents]
        
        missing_count = 0
        for req_type in required_types:
            if req_type not in document_types:
                missing_count += 1
        
        # Score based on percentage of missing documents
        return (missing_count / len(required_types)) * 100
    
    def _check_fraud_signals(self, documents: List[Document]) -> float:
        """Check for fraud signals from LLM validation (0-100)"""
        fraud_score = 0.0
        signal_count = 0
        
        for doc in documents:
            if doc.validation_results:
                signals = doc.validation_results.get("fraud_signals", [])
                mismatches = doc.validation_results.get("mismatches", {})
                
                if signals:
                    fraud_score += len(signals) * 25  # Each signal adds 25 points
                    signal_count += len(signals)
                
                if mismatches:
                    fraud_score += len(mismatches) * 15  # Each mismatch adds 15 points
        
        return min(100.0, fraud_score)
    
    def _generate_reasoning(self, score: float, risk_factors: Dict, decision: str) -> str:
        """Generate human-readable reasoning"""
        reasoning_parts = [f"Risk Score: {score:.1f}/100. Decision: {decision.upper()}."]
        
        # Add top risk factors
        sorted_factors = sorted(
            risk_factors.items(),
            key=lambda x: x[1]["contribution"],
            reverse=True
        )
        
        top_factors = sorted_factors[:3]
        if top_factors:
            reasoning_parts.append("\nTop Risk Factors:")
            for factor_name, factor_data in top_factors:
                if factor_data["contribution"] > 0:
                    reasoning_parts.append(
                        f"- {factor_name.replace('_', ' ').title()}: "
                        f"{factor_data['score']:.1f}% (contributed {factor_data['contribution']:.1f} points)"
                    )
        
        # Add specific issues
        issues = []
        if risk_factors.get("name_mismatch", {}).get("score", 0) > 50:
            issues.append("Name inconsistencies detected across documents")
        if risk_factors.get("dob_mismatch", {}).get("score", 0) > 50:
            issues.append("Date of birth mismatches found")
        if risk_factors.get("address_mismatch", {}).get("score", 0) > 50:
            issues.append("Address inconsistencies detected")
        if risk_factors.get("low_ocr_confidence", {}).get("score", 0) > 50:
            issues.append("Low OCR confidence - document quality may be poor")
        if risk_factors.get("missing_documents", {}).get("score", 0) > 0:
            issues.append("Some required documents are missing")
        
        if issues:
            reasoning_parts.append("\nIssues Identified:")
            for issue in issues:
                reasoning_parts.append(f"- {issue}")
        
        return "\n".join(reasoning_parts)

