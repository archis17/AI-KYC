# Quick Fix: Connection Error in n8n Workflow

## The Problem

You're getting: "The connection cannot be established" or "The service refused the connection"

## Root Cause

Your backend is only listening on `127.0.0.1:8000` (localhost), which Docker containers cannot access.

## The Fix (2 Steps)

### Step 1: Restart Backend with Correct Host Binding

**Stop your current backend** (press Ctrl+C), then restart it with:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Important**: The `--host 0.0.0.0` flag makes the backend accessible from Docker containers.

### Step 2: Update n8n Workflow URLs

In the n8n UI:

1. Open your workflow
2. Click **"Approve Action"** node
3. Set URL to: `http://172.17.0.1:8000/api/admin/applications/={{ $json.body.application_id }}/approve`
4. Click **"Reject Action"** node  
5. Set URL to: `http://172.17.0.1:8000/api/admin/applications/={{ $json.body.application_id }}/reject`
6. **Save** the workflow

## Verify It Works

Test the connection:

```bash
# From your host machine
curl http://localhost:8000/docs

# From inside Docker (should also work now)
docker exec kyc-n8n wget -qO- --timeout=2 http://172.17.0.1:8000/docs | head -3
```

Both should work now!

## Why This Works

- `--host 0.0.0.0` makes backend listen on all network interfaces
- `172.17.0.1` is Docker's bridge gateway IP that containers use to reach the host
- Together, they allow n8n (in Docker) to connect to your backend (on host)

