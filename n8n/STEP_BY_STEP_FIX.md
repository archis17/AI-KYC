# Step-by-Step Fix for Authorization Error

Follow these steps **in order**:

## Step 1: Verify Backend is Running

```bash
curl http://localhost:8000/docs
```

If this fails, start your backend:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 2: Set API Key in Backend

1. Open `backend/.env` (create it if it doesn't exist)
2. Add this line:
   ```env
   INTERNAL_API_KEY=change-this-in-production-use-secure-random-string
   ```
3. **Save the file**
4. **Restart your backend** (Ctrl+C and start again)

## Step 3: Test the Endpoint Manually

From your terminal:
```bash
curl -X POST http://localhost:8000/api/admin/internal/applications/1/approve \
  -H "X-API-Key: change-this-in-production-use-secure-random-string" \
  -H "Content-Type: application/json"
```

**Expected response**: `{"message":"Application approved","application_id":1}` or a 404 if application doesn't exist.

If you get 401, the API key is wrong. If you get connection refused, backend isn't running.

## Step 4: Update n8n Workflow

### For "Approve Action" Node:

1. Open n8n UI → Your workflow
2. Click on **"Approve Action"** node
3. Check these settings:

   **URL**:
   ```
   http://172.17.0.1:8000/api/admin/internal/applications/={{ $json.body.application_id }}/approve
   ```
   (Must have `/internal/` in the path!)

   **Authentication**: `None`

   **Send Headers**: ✅ ON

   **Headers** (click "Add Header" for each):
   - Name: `X-API-Key`
     Value: `change-this-in-production-use-secure-random-string`
   - Name: `Content-Type`
     Value: `application/json`

4. Click **"Save"** on the node

### For "Reject Action" Node:

1. Click on **"Reject Action"** node
2. Check these settings:

   **URL**:
   ```
   http://172.17.0.1:8000/api/admin/internal/applications/={{ $json.body.application_id }}/reject
   ```

   **Authentication**: `None`

   **Send Headers**: ✅ ON

   **Headers**:
   - Name: `X-API-Key`
     Value: `change-this-in-production-use-secure-random-string`
   - Name: `Content-Type`
     Value: `application/json`

   **Send Body**: ✅ ON
   **Body Content Type**: `JSON`
   **JSON Body**:
   ```json
   {
     "reason": "{{ $json.body.reasoning }}"
   }
   ```

3. Click **"Save"** on the node

## Step 5: Save and Test Workflow

1. Click **"Save"** (top right) to save the entire workflow
2. Make sure workflow is **Activated** (green toggle)
3. Test with:
   ```bash
   curl -X POST http://localhost:5678/webhook/kyc-process \
     -H "Content-Type: application/json" \
     -d '{
       "application_id": 1,
       "risk_score": 25,
       "decision": "approved",
       "reasoning": "Test",
       "risk_factors": {}
     }'
   ```

## Common Mistakes

❌ **Wrong URL**: Using `/api/admin/applications/...` instead of `/api/admin/internal/applications/...`
❌ **Missing Header**: Not adding `X-API-Key` header
❌ **Wrong Header Name**: Using `X-API-KEY` or `x-api-key` (should be `X-API-Key`)
❌ **API Key Mismatch**: Value in n8n doesn't match value in `.env`
❌ **Backend Not Restarted**: Changed `.env` but didn't restart backend
❌ **Headers Not Enabled**: "Send Headers" is OFF

## Verification Checklist

- [ ] Backend is running on port 8000
- [ ] `INTERNAL_API_KEY` is set in `backend/.env`
- [ ] Backend was restarted after setting API key
- [ ] curl test works (Step 3)
- [ ] n8n workflow URLs use `/internal/` path
- [ ] `X-API-Key` header is added in both nodes
- [ ] Header value matches `.env` value exactly
- [ ] "Send Headers" is ON in both nodes
- [ ] Workflow is saved and activated

If all checked, the workflow should work! 🎉

