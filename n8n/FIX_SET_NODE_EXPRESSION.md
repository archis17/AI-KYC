# Fix: Set Node Expression Syntax

## The Problem

In the "Prepare Approve URL" Set node, the expression syntax might be incorrect. n8n Set nodes need proper expression syntax.

## Correct Syntax for Set Node

In n8n Set nodes, when setting a field value, use one of these formats:

### Option 1: Simple Expression (Recommended)
```
=http://172.17.0.1:8000/api/admin/internal/applications/{{ $json.body.application_id }}/approve
```

### Option 2: Full Expression with Template Literal
```
={{ `http://172.17.0.1:8000/api/admin/internal/applications/${$json.body.application_id}/approve` }}
```

### Option 3: String Concatenation
```
={{ 'http://172.17.0.1:8000/api/admin/internal/applications/' + $json.body.application_id + '/approve' }}
```

## How to Fix in n8n UI

1. Click on "Prepare Approve URL" node
2. In the "approve_url" field value, change it to:
   ```
   =http://172.17.0.1:8000/api/admin/internal/applications/{{ $json.body.application_id }}/approve
   ```
   OR
   ```
   ={{ `http://172.17.0.1:8000/api/admin/internal/applications/${$json.body.application_id}/approve` }}
   ```
3. Make sure the field type is "String"
4. Do the same for "Prepare Reject URL" node with the reject URL
5. Save the workflow

## Testing

After fixing, test the workflow:
1. Execute the workflow
2. Click on "Prepare Approve URL" node
3. Check the OUTPUT panel - it should show `approve_url` with the actual URL containing the real `application_id` (not the expression)

If the output shows the correct URL with a number instead of `{{ $json.body.application_id }}`, it's working!

