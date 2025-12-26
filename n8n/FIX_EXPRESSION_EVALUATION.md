# Fix: Expression Not Evaluating in URL

## The Problem

The expression `={{ $json.body.application_id }}` in the HTTP Request URL is being sent literally instead of being evaluated. This causes a 422 error because FastAPI tries to parse `={{ $json.body.application_id }}` as an integer.

## The Solution

I've updated the workflow to use **Set nodes** that prepare the URLs first, then the HTTP Request nodes use those prepared URLs. This ensures expressions are properly evaluated.

## What Changed

The workflow now has:
1. **"Prepare Approve URL"** Set node - Creates the approve URL with the expression
2. **"Approve Action"** HTTP Request - Uses the prepared URL
3. **"Prepare Reject URL"** Set node - Creates the reject URL with the expression  
4. **"Reject Action"** HTTP Request - Uses the prepared URL

## How It Works

1. Webhook receives data with `application_id`
2. IF node checks decision
3. **Set node** evaluates: `` `http://172.17.0.1:8000/api/admin/internal/applications/${$json.body.application_id}/approve` ``
4. HTTP Request uses: `={{ $json.approve_url }}` (simple reference, always works)

## If You Need to Update Manually

If the workflow JSON import doesn't work, you can add the Set nodes manually:

### For Approve Path:

1. Add **"Set"** node between "If Approved" and "Approve Action"
2. Configure:
   - **Name**: `approve_url`
   - **Value**: `` `http://172.17.0.1:8000/api/admin/internal/applications/${$json.body.application_id}/approve` ``
3. In "Approve Action" HTTP Request:
   - **URL**: `={{ $json.approve_url }}`

### For Reject Path:

1. Add **"Set"** node between "If Rejected" and "Reject Action"
2. Configure:
   - **Name**: `reject_url`
   - **Value**: `` `http://172.17.0.1:8000/api/admin/internal/applications/${$json.body.application_id}/reject` ``
3. In "Reject Action" HTTP Request:
   - **URL**: `={{ $json.reject_url }}`

## Why This Works

- Set nodes always evaluate expressions properly
- HTTP Request nodes can reliably reference simple JSON paths like `$json.approve_url`
- Template literals (backticks) in Set nodes properly interpolate variables
- This is more reliable than trying to evaluate expressions directly in URL fields

The updated workflow JSON has been saved. Re-import it or update your workflow manually using the steps above.

