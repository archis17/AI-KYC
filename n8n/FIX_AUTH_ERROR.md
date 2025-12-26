# Fix: "Authorization failed" Error in n8n Workflow

## Problem

You're getting: "Authorization failed - please check your credentials" in the "Approve Action" or "Reject Action" nodes.

## Root Cause

The admin endpoints require JWT authentication with an admin user, which is complex for automated workflows.

## Solution

I've created **internal endpoints** that use API key authentication instead of JWT. These are designed for automated workflows like n8n.

### Step 1: Set API Key in Backend

1. Open `backend/.env` (or create it if it doesn't exist)
2. Add this line:
   ```env
   INTERNAL_API_KEY=your-secure-random-api-key-here
   ```
3. Generate a secure random string:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
4. Restart your backend

### Step 2: Update n8n Workflow

In the n8n UI:

1. **Open your workflow**
2. **Click on "Approve Action" node**
3. **Update the URL** to:
   ```
   http://172.17.0.1:8000/api/admin/internal/applications/={{ $json.body.application_id }}/approve
   ```
4. **Add Header**:
   - Click on "Headers" section
   - Add header: `X-API-Key` with value: `your-secure-random-api-key-here` (same as in .env)
   - Keep `Content-Type: application/json`
5. **Click on "Reject Action" node**
6. **Update the URL** to:
   ```
   http://172.17.0.1:8000/api/admin/internal/applications/={{ $json.body.application_id }}/reject
   ```
7. **Add Header**:
   - Add header: `X-API-Key` with value: `your-secure-random-api-key-here`
   - Keep `Content-Type: application/json`
8. **Save the workflow**

### Step 3: Verify

Test the workflow - it should now work without authentication errors!

## What Changed

- **New endpoints**: `/api/admin/internal/applications/{id}/approve` and `/reject`
- **API key auth**: Uses `X-API-Key` header instead of JWT
- **Simpler**: No need to authenticate first, just include the API key

## Security Note

⚠️ **Important**: Change the default API key in production! Use a strong, random string.

```bash
# Generate a secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Then update both:
- `backend/.env`: `INTERNAL_API_KEY=...`
- n8n workflow headers: `X-API-Key: ...`

