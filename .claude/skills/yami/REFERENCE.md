# Yami CLI Complete Reference

## Global Options

```
--uri, -u       Milvus server URI (env: MILVUS_URI)
--token, -t     Authentication token (env: MILVUS_TOKEN)
--db, -d        Database name
--profile, -p   Connection profile name
--mode, -m      Output mode: human | agent
--output, -o    Output format: table | json | yaml
--quiet, -q     Suppress non-data output
```

## Commands

### collection - Collection Operations

```bash
# List all collections
yami collection list

# Create collection (quick mode)
yami collection create <name> --dim <int> [--metric COSINE|L2|IP]

# Create collection with custom fields (DSL)
yami collection create <name> \
  --field "id:int64:pk:auto" \
  --field "title:varchar:256" \
  --field "vec:float_vector:768:COSINE"

# Describe collection
yami collection describe <name>

# Check if collection exists
yami collection has <name>

# Get collection statistics
yami collection stats <name>

# Rename collection
yami collection rename <old_name> <new_name>

# Drop collection
yami collection drop <name> [--force]

# Add field (Milvus 2.6+, must be nullable)
yami collection add-field <collection> "field_name:type:nullable"
```

### index - Index Operations

```bash
yami index list <collection>
yami index describe <collection> <index_name>
yami index create <collection> <field_name> [--type IVF_FLAT|HNSW|...] [--metric L2|IP|COSINE]
yami index drop <collection> <index_name> [--force]
```

### partition - Partition Operations

```bash
yami partition list <collection>
yami partition create <collection> <partition_name>
yami partition has <collection> <partition_name>
yami partition stats <collection> <partition_name>
yami partition drop <collection> <partition_name> [--force]
```

### data - Data Operations

```bash
# Insert data (SQL mode using DuckDB)
yami data insert <collection> --sql "SELECT * FROM 'file.parquet'"
yami data insert <collection> --sql "SELECT * FROM read_json('file.json')"

# Insert with inline JSON
yami data insert <collection> --data '[{"id": 1, "vec": [...]}]'

# Upsert data
yami data upsert <collection> --sql "SELECT * FROM 'file.parquet'"

# Delete by IDs
yami data delete <collection> --ids 1,2,3 [--force]

# Delete by filter
yami data delete <collection> --filter "category == 'old'" [--force]
```

### query - Query Operations

```bash
# Vector search
yami query search <collection> --vector "[0.1, 0.2, ...]" --limit 10
yami query search <collection> --sql "SELECT embedding FROM 'data.parquet' WHERE id=1"
yami query search <collection> --random --limit 10

# Search with filter
yami query search <collection> --random --filter "category == 'A'" --output-fields "id,title"

# Hybrid search (multi-vector)
yami query hybrid-search <collection> \
  --req '{"field": "dense", "vector": [...], "limit": 20}' \
  --req '{"field": "sparse", "vector": {...}, "limit": 20}' \
  --ranker weighted --weights "0.7,0.3"

# Scalar query
yami query query <collection> --filter "age > 20" --limit 100
yami query query <collection> --ids 1,2,3

# Get by IDs (shorthand)
yami query get <collection> 1,2,3
```

### load - Load/Release Operations

```bash
yami load collection <name>
yami load partitions <collection> p1,p2
yami load release <collection>
yami load state <collection>
yami load refresh <collection>
```

### database - Database Operations

```bash
yami database list
yami database describe <name>
yami database create <name>
yami database drop <name> [--force]
```

### alias - Alias Operations

```bash
yami alias list [collection]
yami alias describe <alias>
yami alias create <collection> <alias>
yami alias alter <alias> <new_collection>
yami alias drop <alias> [--force]
```

### io - Import/Export

```bash
# Export to Parquet
yami io export <collection> <output_dir> [--filter "..."] [--fields "id,name,vec"]

# Import from Parquet
yami io import <collection> <path>
yami io import <collection> <dir> --sql "SELECT * FROM data WHERE score > 10"
```

### flush - Flush Operations

```bash
yami flush collection <name>
yami flush all
```

### compact - Compaction Operations

```bash
yami compact run <collection>
yami compact state <job_id>
yami compact wait <job_id>
yami compact list
```

### segment - Segment Information

```bash
yami segment loaded <collection>
yami segment persistent <collection>
yami segment stats <collection>
```

### server - Server Information

```bash
yami server version
yami server type
yami server info
```

### config - Configuration

```bash
yami config init
yami config list
yami config get <key>
yami config set <key> <value>

# Profiles
yami config profile list
yami config profile add <name> --uri <uri> [--token <token>]
yami config profile use <name>
yami config profile remove <name> [--force]
```

## Examples

### Create and populate a collection

```bash
# Create collection
yami --mode agent collection create products --dim 768 --metric COSINE

# Insert data from Parquet
yami --mode agent data insert products --sql "SELECT * FROM 'products.parquet'"

# Search for similar products
yami --mode agent query search products --random --limit 5
```

### Query with filters

```bash
# Find products in category with high score
yami --mode agent query query products \
  --filter "category == 'electronics' and score > 0.8" \
  --limit 20
```

### Export and import data

```bash
# Export collection
yami --mode agent io export products ./backup/

# Import to new collection
yami --mode agent collection create products_v2 --dim 768
yami --mode agent io import products_v2 ./backup/
```
