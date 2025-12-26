# Fix: "The service refused the connection" Error

## Problem

You're seeing this error in the "Approve Action" or "Reject Action" nodes:
```
The service refused the connection - perhaps it is offline
```

## Root Cause

n8n runs inside a Docker container. When it tries to connect to `localhost:8000`, it's looking for a service inside the container, not on your host machine where your backend actually runs.

## Solution

### Option 1: Use Docker Gateway IP (Recommended - Works Immediately)

The Docker bridge gateway IP `172.17.0.1` should work without recreating containers.

**Update Workflow URLs in n8n UI:**

1. **Open your workflow** in n8n
2. **Click on "Approve Action" node**
3. **Change the URL** to:
   ```
   http://172.17.0.1:8000/api/admin/applications/={{ $json.body.application_id }}/approve
   ```
4. **Click on "Reject Action" node**
5. **Change the URL** to:
   ```
   http://172.17.0.1:8000/api/admin/applications/={{ $json.body.application_id }}/reject
   ```
6. **Save the workflow** (Ctrl+S or click Save)

### Option 2: Recreate Container for host.docker.internal

If you prefer using `host.docker.internal`, you need to **recreate** (not just restart) the container:

```bash
cd /home/archis/Desktop/Ai-KYC
docker-compose down n8n
docker-compose up -d n8n
```

Wait about 15 seconds, then update URLs to use `host.docker.internal:8000` instead of `172.17.0.1:8000`.

### Step 3: Fix Backend Binding (CRITICAL!)

**The Problem**: Your backend is only listening on `127.0.0.1` (localhost), which Docker containers cannot access.

**The Solution**: Restart your backend with `--host 0.0.0.0` to bind to all interfaces:

1. **Stop your current backend** (Ctrl+C in the terminal where it's running)

2. **Restart with the correct host binding**:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Verify it's listening on all interfaces**:
   ```bash
   netstat -tlnp | grep :8000
   # Should show: 0.0.0.0:8000 (not 127.0.0.1:8000)
   ```

Now the backend will be accessible from Docker containers!

### Step 4: Test the Workflow

Test the workflow again. The connection should now work!

## Why `host.docker.internal`?

- `localhost` inside a Docker container = the container itself
- `host.docker.internal` = special hostname that points to the host machine
- This allows containers to access services running on the host

## Alternative Solutions

If `host.docker.internal` doesn't work on your system:

1. **Use your machine's IP address**:
   ```bash
   ip addr show | grep "inet " | grep -v 127.0.0.1
   ```
   Then use `http://<your-ip>:8000/...` in the workflow

2. **Use Docker bridge network IP**:
   - Usually `172.17.0.1` (Docker's default gateway)
   - Use `http://172.17.0.1:8000/...` in the workflow

3. **Run backend in Docker too**:
   - Add backend service to docker-compose.yml
   - Use service name (e.g., `http://backend:8000/...`) in workflow
   - Both services will be on the same Docker network

## Verification

After fixing, test with:

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

Check the n8n execution log - it should now successfully connect to your backend!

