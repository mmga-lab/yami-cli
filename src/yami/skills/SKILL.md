---
name: yami
description: Use yami CLI for Milvus vector database operations. Trigger when user wants to manage Milvus collections, insert vectors, search, or query data.
---

# Yami - Milvus CLI Tool

Yami is a command-line interface for Milvus vector database. Default output is JSON (agent mode).

## Command Reference

See [REFERENCE.md](./REFERENCE.md) for complete command documentation.

## Common Operations

### List Collections
```bash
yami collection list
```

### Create Collection
```bash
yami collection create <name> --dim <dimension> [--metric COSINE|L2|IP]
```

### Describe Collection
```bash
yami collection describe <name>
```

### Insert Data
```bash
# From Parquet file
yami data insert <collection> --sql "SELECT * FROM 'data.parquet'"

# From JSON file
yami data insert <collection> --sql "SELECT * FROM read_json('data.json')"
```

### Vector Search
```bash
# Random vector for testing
yami query search <collection> --random --limit 10

# With filter
yami query search <collection> --random --filter "category == 'A'" --limit 10
```

### Scalar Query
```bash
yami query query <collection> --filter "id > 100" --limit 10
yami query get <collection> 1,2,3
```

### Drop Collection
```bash
yami collection drop <name> --force
```

## Output Format

Default is agent mode (JSON output):

**Data queries return JSON directly:**
```bash
yami collection list
# ["collection1", "collection2", ...]

yami collection describe my_col
# {"collection_name": "my_col", "fields": [...], ...}
```

**Operations return status:**
```json
{"status": "success", "message": "Collection 'my_col' dropped successfully"}
```

**Errors return structured error:**
```json
{"error": {"code": "ERROR", "message": "..."}}
```

For human-readable table output, use `--mode human` or `YAMI_MODE=human`.

## Global Options

| Option | Description |
|--------|-------------|
| `--mode human` | Enable human-readable table output |
| `--uri <uri>` | Milvus server URI |
| `--token <token>` | Authentication token |
| `--force` | Skip confirmation prompts |
