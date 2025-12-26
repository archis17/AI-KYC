# Quick Manual n8n Workflow Setup

If you're getting the "propertyValues[itemName] is not iterable" error, create the workflow manually. This takes about 5 minutes.

## Step-by-Step Manual Creation

### 1. Access n8n
- Go to `http://localhost:5678`
- Login: `admin` / `admin`

### 2. Create New Workflow
- Click **"Workflows"** → **"+"** → **"Add workflow"**

### 3. Add Webhook Node
1. Click **"Add node"** (or press `+`)
2. Search for **"Webhook"** and select it
3. Configure:
   - **HTTP Method**: `POST`
   - **Path**: `kyc-process`
   - **Response Mode**: Select **"Respond to Webhook"**
4. **Copy the webhook URL** shown (e.g., `http://localhost:5678/webhook/kyc-process`)
5. Click **"Save"**

### 4. Add First IF Node (For Approved)
1. Click **"Add node"** after Webhook
2. Search for **"IF"** and select it
3. Configure:
   - **Condition**: Click **"Add condition"**
   - **Value 1**: Click and select **"Expression"**, enter: `{{ $json.body.decision }}`
   - **Operation**: `equals`
   - **Value 2**: `approved`
4. Connect: Webhook → IF node

### 5. Add HTTP Request (Approve Action)
1. Click **"Add node"** after the IF node
2. Search for **"HTTP Request"** and select it
3. Configure:
   - **Method**: `POST`
   - **URL**: `http://172.17.0.1:8000/api/admin/internal/applications/={{ $json.body.application_id }}/approve`
   - **Authentication**: None (or Generic with Header Auth)
   - **Headers**: 
     - `X-API-Key`: `your-api-key-from-backend-env`
     - `Content-Type`: `application/json`
   - **Note**: Use `172.17.0.1` (Docker gateway) and the `/internal/` endpoint for API key auth
   - **Authentication**: `None`
   - **Send Headers**: ON
   - **Headers**: Add `Content-Type: application/json`
   - **Send Body**: ON
   - **Body Content Type**: `JSON`
   - **JSON Body**: `{}` (empty object)
4. Connect: IF node (TRUE output) → HTTP Request

### 6. Add Second IF Node (For Rejected)
1. Click **"Add node"** after Webhook (parallel to first IF)
2. Search for **"IF"** and select it
3. Configure:
   - **Condition**: Click **"Add condition"**
   - **Value 1**: Expression `{{ $json.body.decision }}`
   - **Operation**: `equals`
   - **Value 2**: `rejected`
4. Connect: Webhook → IF node (second connection)

### 7. Add HTTP Request (Reject Action)
1. Click **"Add node"** after the second IF node
2. Search for **"HTTP Request"** and select it
3. Configure:
   - **Method**: `POST`
   - **URL**: `http://172.17.0.1:8000/api/admin/internal/applications/={{ $json.body.application_id }}/reject`
   - **Authentication**: None (or Generic with Header Auth)
   - **Headers**: 
     - `X-API-Key`: `your-api-key-from-backend-env`
     - `Content-Type`: `application/json`
   - **Body**: JSON `{ "reason": "{{ $json.body.reasoning }}" }`
   - **Note**: Use `172.17.0.1` (Docker gateway) and the `/internal/` endpoint for API key auth
   - **Authentication**: `None`
   - **Send Headers**: ON
   - **Headers**: Add `Content-Type: application/json`
   - **Send Body**: ON
   - **Body Content Type**: `JSON`
   - **JSON Body**: `{ "reason": "{{ $json.body.reasoning }}" }`
4. Connect: IF node (TRUE output) → HTTP Request

### 8. Add Respond to Webhook
1. Click **"Add node"** after both HTTP Request nodes
2. Search for **"Respond to Webhook"** and select it
3. Configure:
   - **Respond With**: `JSON`
   - **Response Body**: `{ "status": "processed", "application_id": "{{ $json.body.application_id }}" }`
4. Connect: Both HTTP Request nodes → Respond to Webhook

### 9. Save and Activate
1. Click **"Save"** (top right, or Ctrl+S)
2. **Toggle "Active"** to ON (top right, should turn green)
3. The workflow is now ready!

## Visual Flow

```
Webhook (POST /kyc-process)
    ├─→ IF (decision == "approved")
    │   └─→ HTTP Request (Approve)
    │       └─→ Respond to Webhook
    │
    └─→ IF (decision == "rejected")
        └─→ HTTP Request (Reject)
            └─→ Respond to Webhook
```

## Test the Workflow

After activating, test with:

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

You should see the workflow execute in n8n's execution history.

## Notes

- **Backend URL**: Since n8n runs in Docker and backend runs on host, use `http://172.17.0.1:8000` (Docker bridge gateway IP, NOT `localhost:8000`)
- **Internal Endpoints**: Use `/api/admin/internal/...` endpoints (not `/api/admin/...`) - these use API key auth instead of JWT
- **API Key**: Set `INTERNAL_API_KEY` in `backend/.env` and use the same value in the `X-API-Key` header
- **Webhook URL**: Make sure your backend `.env` has `N8N_WEBHOOK_URL=http://localhost:5678/webhook/kyc-process`
- **Activation**: The workflow MUST be activated (green toggle) to receive webhooks
- **Security**: Generate a secure API key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`


