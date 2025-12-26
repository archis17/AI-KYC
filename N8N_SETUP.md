# n8n Workflow Setup Guide

## Why the Workflow Didn't Start

The n8n workflow didn't start because it needs to be **imported and activated** in the n8n UI. Simply having the workflow JSON file and running the n8n container is not enough - you need to manually set it up in the n8n interface.

## Prerequisites

1. ✅ n8n container is running (verified: `docker-compose ps` shows `kyc-n8n` is up)
2. ✅ n8n is accessible at `http://localhost:5678` (verified: health check passed)
3. ⚠️ Workflow needs to be imported and activated

## Step-by-Step Setup

### 1. Access n8n UI

Open your browser and navigate to:
```
http://localhost:5678
```

### 2. Login to n8n

- **Username**: `admin`
- **Password**: `admin`

(These credentials are set in `docker-compose.yml`)

### 3. Import the Workflow

**Option A: Import from File (if JSON import works)**

1. Click on **"Workflows"** in the left sidebar
2. Click the **"+"** button or **"Add workflow"**
3. Click the **three dots menu (⋮)** in the top right
4. Select **"Import from File"** or **"Import from URL"**
5. Navigate to and select: `n8n/workflows/kyc-workflow.json`
   - Or copy the file path: `/home/archis/Desktop/Ai-KYC/n8n/workflows/kyc-workflow.json`
6. Click **"Import"**

**Option B: Create Manually (Recommended if import fails)**

If you get the "propertyValues[itemName] is not iterable" error, create the workflow manually:

1. Click **"Workflows"** → **"+"** → **"Add workflow"**
2. Click **"Add node"** and search for **"Webhook"**
3. Configure Webhook:
   - **HTTP Method**: POST
   - **Path**: `kyc-process`
   - **Response Mode**: "Respond to Webhook"
   - Copy the webhook URL shown (should be `http://localhost:5678/webhook/kyc-process`)
4. Add **"IF"** node (search "If")
   - Connect from Webhook
   - Condition: `{{ $json.body.decision }}` equals `approved`
5. Add **"HTTP Request"** node (for approved path)
   - Connect from "If Approved" TRUE output
   - **Method**: POST
   - **URL**: `http://localhost:8000/api/admin/applications/={{ $json.body.application_id }}/approve`
   - **Headers**: `Content-Type: application/json`
   - **Body**: JSON (empty object `{}`)
6. Add another **"IF"** node (for rejected)
   - Connect from Webhook
   - Condition: `{{ $json.body.decision }}` equals `rejected`
7. Add **"HTTP Request"** node (for rejected path)
   - Connect from "If Rejected" TRUE output
   - **Method**: POST
   - **URL**: `http://localhost:8000/api/admin/applications/={{ $json.body.application_id }}/reject`
   - **Headers**: `Content-Type: application/json`
   - **Body**: JSON `{ "reason": "{{ $json.body.reasoning }}" }`
8. Add **"Respond to Webhook"** node
   - Connect from both HTTP Request nodes
   - **Response Body**: JSON `{ "status": "processed", "application_id": "{{ $json.body.application_id }}" }`
9. Click **"Save"** (top right)

### 4. Configure the Webhook

After importing, you need to configure the webhook:

1. Click on the **"Webhook"** node in the workflow
2. The webhook should have the ID: `kyc-process`
3. Make sure the webhook path is: `/webhook/kyc-process`
4. The full webhook URL should be: `http://localhost:5678/webhook/kyc-process`

**Important**: The webhook URL in your backend config (`backend/app/core/config.py`) should match:
```python
N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/kyc-process"
```

### 5. Fix Backend URLs in Workflow (CRITICAL - Docker Issue)

**Problem**: n8n runs in Docker, so `localhost:8000` refers to the container, not your host machine where the backend runs.

**Solution**: Use `host.docker.internal:8000` instead of `localhost:8000`

**Steps to Fix:**

1. **First, restart n8n container** to enable host.docker.internal:
   ```bash
   docker-compose restart n8n
   ```

2. **Update the "Approve Action" node**:
   - Click on the **"Approve Action"** node
   - Change URL from `http://localhost:8000/...` to `http://172.17.0.1:8000/...`
   - Full URL: `http://172.17.0.1:8000/api/admin/applications/={{ $json.body.application_id }}/approve`
   - **Note**: `172.17.0.1` is the Docker bridge gateway IP that allows containers to reach the host

3. **Update the "Reject Action" node**:
   - Click on the **"Reject Action"** node
   - Change URL from `http://localhost:8000/...` to `http://172.17.0.1:8000/...`
   - Full URL: `http://172.17.0.1:8000/api/admin/applications/={{ $json.body.application_id }}/reject`

4. **Save the workflow** (Ctrl+S or click Save button)

### 6. Activate the Workflow

**This is the critical step!** The workflow must be **activated** to receive webhook triggers:

1. In the workflow editor, click the **"Active"** toggle in the top right (it should turn green)
2. Or click **"Save"** and then toggle **"Active"** to ON

**The workflow will NOT receive webhooks unless it's activated!**

### 7. Test the Workflow

You can test the webhook manually:

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

You should see the workflow execute in the n8n UI.

## Verification Checklist

- [ ] n8n container is running (`docker-compose ps`)
- [ ] Can access n8n UI at `http://localhost:5678`
- [ ] Logged in with admin/admin
- [ ] Workflow imported from `n8n/workflows/kyc-workflow.json`
- [ ] Webhook node configured with path `/webhook/kyc-process`
- [ ] Backend URLs updated to `http://localhost:8000` (if backend runs outside Docker)
- [ ] **Workflow is ACTIVATED** (green toggle in top right)
- [ ] Backend `.env` has `N8N_WEBHOOK_URL=http://localhost:5678/webhook/kyc-process`

## Troubleshooting

### Import Error: "propertyValues[itemName] is not iterable"

This error occurs when the workflow JSON structure doesn't match your n8n version. **Solution**: Create the workflow manually in the n8n UI (see Option B in step 3 above).

**Why this happens:**
- n8n workflow JSON format changes between versions
- The If node structure is particularly sensitive to version differences
- Imported workflows from older/newer n8n versions may not be compatible

**Quick Fix:**
1. Don't import the JSON file
2. Create the workflow manually in n8n UI (takes 5 minutes)
3. Follow the manual creation steps in Option B above

### Workflow Still Not Triggering?

1. **Check if workflow is activated**: The toggle must be green/ON
2. **Check webhook URL**: Verify it matches in both n8n and backend config
3. **Check n8n logs**: 
   ```bash
   docker logs kyc-n8n
   ```
4. **Check backend logs**: Look for "Error triggering N8N workflow" messages
5. **Test webhook manually**: Use the curl command above
6. **Check network connectivity**: Ensure backend can reach `http://localhost:5678`

### Common Issues

**Issue**: "Connection refused" when backend tries to trigger workflow
- **Solution**: Ensure n8n container is running and accessible

**Issue**: Webhook receives request but workflow doesn't execute
- **Solution**: Check if workflow is activated (most common issue!)

**Issue**: Workflow executes but HTTP requests to backend fail
- **Solution**: Update URLs from `http://backend:8000` to `http://localhost:8000` or use host.docker.internal

**Issue**: "Webhook not found" error
- **Solution**: Verify webhook path is `/webhook/kyc-process` and workflow is activated

## Next Steps

Once the workflow is set up and activated:

1. The backend will automatically trigger it when a KYC application is processed
2. The workflow will receive the risk score and decision
3. Based on the decision, it will call the appropriate backend endpoint
4. You can monitor executions in the n8n UI under "Executions"

## Additional Notes

- n8n stores workflows in the `n8n_data` Docker volume
- Workflows persist even if you restart the container
- You can export workflows from n8n UI if you make changes
- The workflow JSON file is just for initial import - changes in UI don't auto-update the file

