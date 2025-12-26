# Quick Fix: Authorization Error

## The Problem
"Authorization failed - please check your credentials" in n8n workflow

## The Solution (2 Steps)

### Step 1: Set API Key in Backend

Add to `backend/.env`:
```env
INTERNAL_API_KEY=change-this-in-production-use-secure-random-string
```

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Restart your backend** after adding this.

### Step 2: Update n8n Workflow URLs and Headers

In n8n UI:

1. **"Approve Action" node**:
   - URL: `http://172.17.0.1:8000/api/admin/internal/applications/={{ $json.body.application_id }}/approve`
   - Headers: Add `X-API-Key` = `change-this-in-production-use-secure-random-string` (same as .env)

2. **"Reject Action" node**:
   - URL: `http://172.17.0.1:8000/api/admin/internal/applications/={{ $json.body.application_id }}/reject`
   - Headers: Add `X-API-Key` = `change-this-in-production-use-secure-random-string`
   - Body: JSON `{ "reason": "{{ $json.body.reasoning }}" }`

3. **Save** the workflow

## What Changed

- ✅ New `/internal/` endpoints created (no JWT needed)
- ✅ API key authentication instead of user login
- ✅ Simpler for automated workflows

## Security

⚠️ **Change the default API key!** Use the generated secure string in both:
- `backend/.env`
- n8n workflow headers

Done! The workflow should now work. 🎉

