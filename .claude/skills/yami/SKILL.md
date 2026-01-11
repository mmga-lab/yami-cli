---
name: yami
description: Use yami CLI for Milvus vector database operations. Trigger when user wants to manage Milvus collections, insert vectors, search, or query data.
---

# Yami - Milvus CLI Tool

Yami is a command-line interface for Milvus vector database.

## Setup (Optional)

```bash
# Set environment variable for JSON output
export YAMI_MODE=agent
```

## Common Operations

### Collection Management
```bash
yami collection list
yami collection create <name> --dim <dimension> [--metric COSINE|L2|IP]
yami collection describe <name>
yami collection has <name>
yami collection stats <name>
yami collection drop <name> --force
```

### Load Collection (required before search)
```bash
yami load <collection>
```

### Insert Data

```bash
# From file
yami data insert <collection> --sql "SELECT * FROM 'data.parquet'"
yami data insert <collection> --sql "SELECT * FROM read_json('data.json')"

# Random test data (DuckDB SQL)
# 100 rows, 128-dim vectors:
yami data insert <collection> --sql "SELECT range AS id, list_transform(generate_series(1, 128), x -> random()) AS vector FROM range(100)"
```

### Vector Search
```bash
# Random vector search (specify --dim matching collection)
yami query search <collection> --random --dim <dimension> --limit 10

# With filter
yami query search <collection> --random --dim 128 --filter "category == 'A'" --limit 10
```

### Scalar Query
```bash
yami query query <collection> --filter "id >= 0" --limit 100
yami query get <collection> 1,2,3
```

## Output Format

With `YAMI_MODE=agent` or `--mode agent`:

```bash
# Data queries return JSON directly (array or object)
yami --mode agent collection list
# Output: ["collection1", "collection2", ...]

yami --mode agent collection describe my_col
# Output: {"collection_name": "my_col", "fields": [...], ...}

# Operations return status message
yami --mode agent collection drop my_col --force
# Output: {"status": "success", "message": "Collection 'my_col' dropped successfully"}

# Errors return structured error
yami --mode agent collection describe nonexistent
# Output: {"error": {"code": "ERROR", "message": "..."}}
```

## Complete Reference

See [REFERENCE.md](./REFERENCE.md) for all commands.
