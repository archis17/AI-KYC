# Troubleshooting: Authorization Failed Error

## Check These Steps

### 1. Is Backend Running?

```bash
curl http://localhost:8000/docs
```

If this fails, **start your backend**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Is API Key Set in Backend?

Check `backend/.env` has:
```env
INTERNAL_API_KEY=change-this-in-production-use-secure-random-string
```

**Restart backend** after adding/updating this.

### 3. Are You Using the Correct Endpoint?

The workflow should use:
- ✅ `http://172.17.0.1:8000/api/admin/internal/applications/...`
- ❌ NOT `http://172.17.0.1:8000/api/admin/applications/...` (old endpoint)

### 4. Is the Header Name Correct?

In n8n workflow, the header must be:
- **Name**: `X-API-Key` (exactly this, case-sensitive in n8n)
- **Value**: `change-this-in-production-use-secure-random-string` (same as in .env)

### 5. Test the Endpoint Manually

From your host machine:
```bash
curl -X POST http://localhost:8000/api/admin/internal/applications/1/approve \
  -H "X-API-Key: change-this-in-production-use-secure-random-string" \
  -H "Content-Type: application/json"
```

If this works, the endpoint is correct. If it fails, check backend logs.

### 6. Check n8n Execution Logs

In n8n UI:
1. Go to "Executions"
2. Click on the failed execution
3. Check the "Approve Action" node
4. Look at the request/response details
5. Verify the headers are being sent correctly

### 7. Common Issues

**Issue**: Header not being sent
- **Fix**: In n8n, make sure "Send Headers" is ON
- Check the header is in the "Header Parameters" section

**Issue**: Wrong API key value
- **Fix**: The value in n8n must EXACTLY match the value in `backend/.env`
- No extra spaces, same case

**Issue**: Backend not restarted
- **Fix**: After changing `.env`, you MUST restart the backend

**Issue**: Using old endpoint
- **Fix**: Make sure URL has `/internal/` in it

### 8. Debug Steps

1. Check backend logs for the incoming request
2. Verify the header is being received
3. Check if `settings.INTERNAL_API_KEY` is loaded correctly
4. Test with curl first, then n8n

## Still Not Working?

1. **Check backend logs** when n8n makes the request
2. **Verify** the exact header name and value in n8n
3. **Test** the endpoint with curl first
4. **Ensure** backend was restarted after code changes

