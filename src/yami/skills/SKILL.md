---
name: yami
description: Use yami CLI for Milvus vector database operations. Trigger when user wants to manage Milvus collections, insert vectors, search, or query data.
---

# Yami - Milvus CLI Tool

Yami is a command-line interface for Milvus vector database. Use `--mode agent` for structured JSON output.

## Quick Start

```bash
# Always use agent mode for structured output
yami --mode agent <command>

# Or set default mode
export YAMI_MODE=agent
```

## Command Reference

See [REFERENCE.md](./REFERENCE.md) for complete command documentation.

## Common Operations

### List Collections
```bash
yami --mode agent collection list
```

### Create Collection
```bash
yami --mode agent collection create <name> --dim <dimension> [--metric COSINE|L2|IP]
```

### Describe Collection
```bash
yami --mode agent collection describe <name>
```

### Insert Data
```bash
# From Parquet file
yami --mode agent data insert <collection> --sql "SELECT * FROM 'data.parquet'"

# From JSON file
yami --mode agent data insert <collection> --sql "SELECT * FROM read_json('data.json')"
```

### Vector Search
```bash
# Random vector for testing
yami --mode agent query search <collection> --random --limit 10

# With filter
yami --mode agent query search <collection> --random --filter "category == 'A'" --limit 10
```

### Scalar Query
```bash
yami --mode agent query query <collection> --filter "id > 100" --limit 10
yami --mode agent query get <collection> 1,2,3
```

### Drop Collection
```bash
yami --mode agent collection drop <name> --force
```

## Output Format

In agent mode, all output is JSON:

**Success:**
```json
{"status": "success", "message": "...", "data": {...}}
```

**Error:**
```json
{"error": {"code": "ERROR", "message": "..."}}
```

**Data:**
```json
[{"id": 1, "name": "..."}, ...]
```

## Global Options

| Option | Description |
|--------|-------------|
| `--mode agent` | Enable agent-friendly JSON output |
| `--uri <uri>` | Milvus server URI |
| `--token <token>` | Authentication token |
| `--force` | Skip confirmation prompts |
