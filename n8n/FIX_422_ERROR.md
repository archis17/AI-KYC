# Fix: 422 Validation Error

## The Problem

You're getting a **422 Unprocessable Entity** error, which means FastAPI couldn't validate the request.

## Common Causes

### 1. Sending Body When Not Expected

The **approve endpoint** doesn't accept a body. Make sure:
- **Send Body**: OFF (unchecked)
- No body content configured

### 2. Invalid Body Format for Reject

The **reject endpoint** expects:
```json
{
  "reason": "string or null"
}
```

Make sure the JSON body is valid.

### 3. Missing or Invalid Headers

Ensure:
- `X-API-Key` header is present
- `Content-Type: application/json` (only if sending body)

## Quick Fix

### For "Approve Action" Node:

1. **Send Body**: Set to **OFF** (unchecked)
2. **Headers**: Keep `X-API-Key` and `Content-Type`
3. **URL**: `http://172.17.0.1:8000/api/admin/internal/applications/={{ $json.body.application_id }}/approve`

### For "Reject Action" Node:

1. **Send Body**: Set to **ON** (checked)
2. **Body Content Type**: `JSON`
3. **JSON Body**:
   ```json
   {
     "reason": "{{ $json.body.reasoning }}"
   }
   ```
   Or if reasoning might be null:
   ```json
   {
     "reason": "{{ $json.body.reasoning || null }}"
   }
   ```

## Test the Endpoints

### Test Approve (no body):
```bash
curl -X POST http://localhost:8000/api/admin/internal/applications/1/approve \
  -H "X-API-Key: change-this-in-production-use-secure-random-string" \
  -H "Content-Type: application/json"
```

### Test Reject (with body):
```bash
curl -X POST http://localhost:8000/api/admin/internal/applications/1/reject \
  -H "X-API-Key: change-this-in-production-use-secure-random-string" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Test rejection"}'
```

## Check n8n Execution Details

In n8n UI:
1. Go to "Executions"
2. Click the failed execution
3. Click "Approve Action" node
4. Check:
   - **Request** tab: See what was actually sent
   - **Response** tab: See the error details
   - Look for validation error messages

## Common Issues

**Issue**: Body sent when endpoint doesn't expect it
- **Fix**: Turn OFF "Send Body" for approve action

**Issue**: Invalid JSON in body
- **Fix**: Check JSON syntax, ensure proper escaping in n8n expressions

**Issue**: Missing required fields
- **Fix**: Ensure `application_id` is in the URL path correctly

**Issue**: Header format wrong
- **Fix**: Headers should be in "Header Parameters" section, not "Authentication"

## Still Getting 422?

1. Check backend logs for detailed validation errors
2. Test endpoints with curl first
3. Verify the exact request n8n is sending (check execution details)
4. Ensure backend code matches the expected format

