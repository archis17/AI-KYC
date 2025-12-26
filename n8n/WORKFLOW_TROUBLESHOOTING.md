# Complete Workflow Troubleshooting Guide

## Issue: Workflow Not Completing

### Primary Cause: Missing "Review" Decision Handling ✅ FIXED

**Problem**: The workflow only handles "approved" and "rejected" decisions, but the backend can also send "review" (risk score 31-60). When decision is "review", neither IF condition matches, so the workflow stops and never reaches "Respond to Webhook".

**Solution**: Added direct connection from Webhook → Log Result, so "review" decisions still complete the workflow.

**Status**: ✅ Fixed in `kyc-workflow.json`

### How to Apply the Fix

1. **Option A: Re-import the workflow** (if JSON import works)
   - Go to n8n UI → Workflows
   - Delete the old workflow
   - Import `n8n/workflows/kyc-workflow.json`

2. **Option B: Manual fix in n8n UI** (if JSON import doesn't work)
   - Open your workflow in n8n
   - Click on "Webhook" node
   - Add a third connection from Webhook to "Log Result"
   - Save the workflow

## Other Common Issues

### 1. Connection Refused Error

**Symptoms**: "The service refused the connection" in HTTP Request nodes

**Cause**: n8n runs in Docker, so `localhost:8000` refers to the container, not your host machine.

**Fix**: 
- Use `172.17.0.1:8000` instead of `localhost:8000` in HTTP Request URLs
- Ensure backend is running with `--host 0.0.0.0` (not just `127.0.0.1`)

**See**: `n8n/FIX_CONNECTION_ERROR.md`

### 2. Authorization Failed Error

**Symptoms**: "Authorization failed" in HTTP Request nodes

**Cause**: Admin endpoints require JWT authentication, which is complex for automated workflows.

**Fix**: 
- Use internal endpoints: `/api/admin/internal/applications/{id}/approve` and `/reject`
- Add `X-API-Key` header with your `INTERNAL_API_KEY` from backend `.env`

**See**: `n8n/FIX_AUTH_ERROR.md`

### 3. 422 Validation Error

**Symptoms**: 422 Unprocessable Entity error from backend

**Causes**:
- Sending body when approve endpoint doesn't expect it
- Invalid JSON format for reject endpoint
- Missing required headers

**Fix**:
- Approve Action: Set "Send Body" to OFF
- Reject Action: Set "Send Body" to ON, use JSON: `{ "reason": "{{ $json.body.reasoning }}" }`
- Ensure `X-API-Key` header is present

**See**: `n8n/FIX_422_ERROR.md`

### 4. Expression Not Evaluating

**Symptoms**: URL contains literal `={{ $json.body.application_id }}` instead of actual ID

**Cause**: n8n sometimes doesn't evaluate expressions directly in URL fields.

**Fix**: Use Set nodes to prepare URLs first, then reference them in HTTP Request nodes.

**See**: `n8n/FIX_EXPRESSION_EVALUATION.md`

### 5. Workflow Not Triggering

**Symptoms**: Backend sends request but workflow doesn't execute

**Checklist**:
- ✅ Workflow is **activated** (toggle must be green/ON)
- ✅ Webhook URL matches: `http://localhost:5678/webhook/kyc-process`
- ✅ Backend config has correct `N8N_WEBHOOK_URL`
- ✅ n8n container is running: `docker ps | grep n8n`
- ✅ Check n8n logs: `docker logs kyc-n8n`

## Testing the Workflow

### Test with Approved Decision
```bash
curl -X POST http://localhost:5678/webhook/kyc-process \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": 1,
    "risk_score": 25,
    "decision": "approved",
    "reasoning": "Low risk",
    "risk_factors": {}
  }'
```

### Test with Rejected Decision
```bash
curl -X POST http://localhost:5678/webhook/kyc-process \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": 1,
    "risk_score": 75,
    "decision": "rejected",
    "reasoning": "High risk",
    "risk_factors": {}
  }'
```

### Test with Review Decision (This was failing before!)
```bash
curl -X POST http://localhost:5678/webhook/kyc-process \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": 1,
    "risk_score": 45,
    "decision": "review",
    "reasoning": "Requires manual review",
    "risk_factors": {}
  }'
```

All three should now complete successfully!

## Verification Checklist

After applying fixes, verify:

- [ ] Workflow is activated (green toggle)
- [ ] All three decision types complete successfully
- [ ] No "Error" executions in n8n execution log
- [ ] Backend receives API calls for approve/reject actions
- [ ] Webhook responds with `{"status": "processed", "application_id": ...}`

## Quick Reference: Decision Values

The backend risk scoring returns:
- `"approved"` - Risk score 0-30 (automatically approved)
- `"review"` - Risk score 31-60 (requires manual review)
- `"rejected"` - Risk score 61-100 (automatically rejected)

The workflow now handles all three cases correctly.

