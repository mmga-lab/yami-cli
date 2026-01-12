---
name: yami
description: Use yami CLI for Milvus vector database operations. Trigger when user wants to manage Milvus collections, insert vectors, search, or query data.
---

# Yami - Milvus CLI Tool

Yami is a command-line interface for Milvus vector database. Default output is JSON (agent mode).

## Command Reference

See [REFERENCE.md](./REFERENCE.md) for complete command documentation.

## Response Format (Agent Mode)

All commands return a unified JSON envelope:

### Success Response
```json
{
  "ok": true,
  "data": <result>,
  "meta": {
    "command": "collection list",
    "duration_ms": 42,
    "count": 5
  }
}
```

### Error Response
```json
{
  "ok": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Collection 'my_col' not found",
    "hint": "Use 'yami collection list' to see available collections"
  }
}
```

## Error Codes

| Code | Description | Common Fix |
|------|-------------|------------|
| `CONNECTION_ERROR` | Cannot connect to server | Check URI and server status |
| `NOT_FOUND` | Resource not found | Verify name with list command |
| `VALIDATION_ERROR` | Invalid input | Check argument format |
| `ALREADY_EXISTS` | Resource exists | Use different name or drop first |
| `AUTHENTICATION_ERROR` | Auth failed | Verify token |
| `FILE_NOT_FOUND` | Input file missing | Check file path |
| `INVALID_FORMAT` | Invalid JSON/SQL | Check syntax |
| `MISSING_ARGUMENT` | Required arg missing | Use --help to see required args |

## Common Operations

### List Collections
```bash
yami collection list
# {"ok": true, "data": ["col1", "col2"], "meta": {...}}
```

### Create Collection
```bash
yami collection create products --dim 768 --metric COSINE
# {"ok": true, "data": {"message": "Collection 'products' created"}, "meta": {...}}
```

### Describe Collection
```bash
yami collection describe products
# {"ok": true, "data": {"collection_name": "products", "fields": [...]}, "meta": {...}}
```

### Insert Data
```bash
# From Parquet file
yami data insert products --sql "SELECT * FROM 'data.parquet'"

# From JSON file
yami data insert products --sql "SELECT * FROM read_json('data.json')"

# Inline JSON
yami data insert products --data '[{"id": 1, "vec": [0.1, 0.2, ...]}]'
```

### Vector Search
```bash
# Random vector for testing
yami query search products --random --limit 10

# With filter
yami query search products --random --filter "category == 'A'" --limit 10

# From vector
yami query search products --vector "[0.1, 0.2, ...]" --limit 10
```

### Scalar Query
```bash
yami query query products --filter "id > 100" --limit 10
yami query get products 1,2,3
```

### Drop Collection (Destructive)
```bash
yami collection drop products --force
# IMPORTANT: Always use --force to avoid interactive prompts
```

## Agent Best Practices

### 1. Always Use --force for Destructive Operations

Destructive operations require confirmation by default. Use `--force` to skip prompts:

```bash
# WRONG - Will hang waiting for input
yami collection drop my_col

# CORRECT - Skips confirmation
yami collection drop my_col --force
yami data delete my_col --filter "age > 50" --force
```

### 2. Check Response Before Processing

Always verify `ok` field before accessing data:

```python
import json
import subprocess

result = subprocess.run(["yami", "collection", "list"], capture_output=True, text=True)
response = json.loads(result.stdout)

if response["ok"]:
    collections = response["data"]
    print(f"Found {len(collections)} collections")
else:
    error = response["error"]
    print(f"Error [{error['code']}]: {error['message']}")
    if error.get("hint"):
        print(f"Hint: {error['hint']}")
```

### 3. Use Meta Information

The `meta` field contains useful information:
- `count`: Number of items returned/affected
- `duration_ms`: Operation time
- `command`: The command that was executed

### 4. Connection Testing

Before running operations, test connection:

```bash
yami connect http://localhost:19530
# {"ok": true, "data": {"uri": "...", "version": "2.5.0"}, "meta": {...}}
```

## Global Options

| Option | Description |
|--------|-------------|
| `--mode human` | Enable human-readable table output |
| `--uri <uri>` | Milvus server URI |
| `--token <token>` | Authentication token |
| `--db <name>` | Database name |
| `--force` | Skip confirmation prompts (REQUIRED for destructive ops) |
| `--quiet` | Suppress non-data output (default in agent mode) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MILVUS_URI` | Default Milvus URI |
| `MILVUS_TOKEN` | Default authentication token |
| `YAMI_MODE` | Default mode: `agent` or `human` |
