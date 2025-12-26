#!/bin/bash
# Test script to verify workflow handles "review" decisions correctly

echo "Testing workflow with 'review' decision..."
echo ""

curl -X POST http://localhost:5678/webhook/kyc-process \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": 999,
    "risk_score": 45,
    "decision": "review",
    "reasoning": "Requires manual review - risk score in middle range",
    "risk_factors": {
      "name_mismatch": {"score": 20, "weight": 25, "contribution": 5},
      "dob_mismatch": {"score": 15, "weight": 20, "contribution": 3}
    }
  }'

echo ""
echo ""
echo "Check n8n UI for execution result - it should show 'Succeeded'"
echo "If it shows 'Error', the workflow needs to be re-imported with the updated JSON"

