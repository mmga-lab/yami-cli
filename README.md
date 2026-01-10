# Yami - Yet Another Milvus Interface

A powerful command-line interface for Milvus vector database.

## Installation

```bash
# Using uv
uv pip install -e .

# Using pip
pip install -e .
```

## Quick Start

```bash
# Test connection
yami connect http://localhost:19530

# List collections
yami --uri http://localhost:19530 collection list

# Create a collection
yami collection create my_collection --dim 768 --metric COSINE

# Insert data
yami data insert my_collection --file data.json

# Search
yami query search my_collection --vector "[0.1, 0.2, ...]" --limit 10

# Query by filter
yami query query my_collection --filter "age > 20"
```

## Configuration

### Connection Profiles

Create connection profiles for easy switching between environments:

```bash
# Add a profile
yami config profile add local --uri http://localhost:19530

# Add a cloud profile
yami config profile add cloud --uri https://xxx.zillizcloud.com --token $TOKEN

# Set default profile
yami config profile use local

# List profiles
yami config profile list
```

### Using Profiles

```bash
# Use default profile
yami collection list

# Use specific profile
yami --profile cloud collection list

# Override with CLI options
yami --uri http://custom:19530 collection list
```

## Commands

### Collection Operations

```bash
yami collection list                    # List all collections
yami collection describe <name>         # Describe a collection
yami collection create <name> --dim N   # Create a collection (quick mode)
yami collection drop <name>             # Drop a collection
yami collection has <name>              # Check if collection exists
yami collection rename <old> <new>      # Rename a collection
yami collection stats <name>            # Get collection statistics
```

#### Create with Field DSL

```bash
# Create with custom fields
yami collection create my_col \
  --field "id:int64:pk:auto" \
  --field "title:varchar:512" \
  --field "embedding:float_vector:768:COSINE"

# Show field DSL syntax
yami collection create --field-help
```

#### Add Field (Milvus 2.6+)

```bash
# Add nullable field
yami collection add-field my_col "score:int64:nullable"

# Add nullable field with default value
yami collection add-field my_col "status:varchar:64:nullable" --default '"active"'

# Add nullable vector field
yami collection add-field my_col "extra_vec:float_vector:128:nullable"
```

### Index Operations

```bash
yami index list <collection>                    # List indexes
yami index describe <collection> <index>        # Describe an index
yami index create <collection> <field>          # Create an index
yami index drop <collection> <index>            # Drop an index
```

### Partition Operations

```bash
yami partition list <collection>        # List partitions
yami partition create <collection> <name>  # Create a partition
yami partition drop <collection> <name>    # Drop a partition
yami partition has <collection> <name>     # Check if partition exists
yami partition stats <collection> <name>   # Get partition statistics
```

### Data Operations

```bash
# Insert from Parquet
yami data insert my_col --sql "SELECT * FROM 'data.parquet'"

# Insert from JSON file
yami data insert my_col --sql "SELECT * FROM read_json('data.json')"

# Insert with transformation
yami data insert my_col --sql "SELECT id, vec FROM 'data.parquet' WHERE score > 0.5"

# Upsert from Parquet
yami data upsert my_col --sql "SELECT * FROM 'updates.parquet'"

# Inline JSON insert
yami data insert my_col --data '[{"id": 1, "vec": [0.1, 0.2, ...]}]'

# Delete by IDs
yami data delete my_col --ids 1,2,3

# Delete by filter
yami data delete my_col --filter "category == 'old'"
```

### Search Operations

#### Vector Search

```bash
# Direct vector input
yami query search my_col --vector "[0.1, 0.2, ...]" --limit 10

# Read vector from Parquet via DuckDB SQL
yami query search my_col --sql "SELECT embedding FROM 'data.parquet' WHERE id=1"

# Batch search from Parquet
yami query search my_col --sql "SELECT embedding FROM 'data.parquet' LIMIT 5"

# Random vector for testing
yami query search my_col --random --limit 10

# With filter and output fields
yami query search my_col --random --filter "category == 'A'" --output-fields "id,title"
```

#### Hybrid Search

Multi-vector search with ranking fusion:

```bash
# RRF ranker (default)
yami query hybrid-search my_col \
  --req "dense_vec:[0.1,0.2,...]:10" \
  --req "sparse_vec:{1:0.5,100:0.3}:10" \
  --ranker rrf --k 60

# Weighted ranker
yami query hybrid-search my_col \
  --req "vec1:[...]:10" \
  --req "vec2:[...]:10" \
  --ranker weighted --weights "0.7,0.3"

# From file
yami query hybrid-search my_col --file requests.json
```

#### Scalar Query

```bash
yami query query <collection> --filter "age > 20"   # Query by filter
yami query query <collection> --ids 1,2,3           # Query by IDs
yami query get <collection> 1,2,3                   # Get by IDs (shorthand)
```

### Import/Export Operations

Export and import data using Parquet format:

```bash
# Export entire collection to directory
yami io export my_col ./export_data

# Export with filter
yami io export my_col ./export_data --filter "category == 'A'"

# Export specific fields
yami io export my_col ./export_data --fields "id,name,embedding"

# Export with custom batch size (rows per file)
yami io export my_col ./export_data --batch-size 50000

# Import from single Parquet file
yami io import my_col data.parquet

# Import from directory (all .parquet files)
yami io import my_col ./export_data/

# Import with SQL transformation
yami io import my_col ./data/ --sql "SELECT id, name, vec FROM data WHERE score > 10"
```

### Database Operations

```bash
yami database list                      # List databases
yami database describe <name>           # Describe a database
yami database create <name>             # Create a database
yami database drop <name>               # Drop a database
yami database use <name>                # Switch database
```

### Load/Release Operations

```bash
yami load collection <name>             # Load collection
yami load partitions <collection> p1,p2 # Load partitions
yami load release <collection>          # Release collection
yami load state <collection>            # Get load state
yami load refresh <collection>          # Refresh load state
```

### Flush Operations

```bash
yami flush collection <name>            # Flush a collection
yami flush all                          # Flush all collections
```

### Compaction Operations

```bash
yami compact run <collection>           # Start compaction
yami compact state <job_id>             # Check compaction state
yami compact wait <job_id>              # Wait for compaction to complete
yami compact list                       # List cached compaction jobs
yami compact clean                      # Clean completed jobs from cache
```

### Segment Operations

```bash
yami segment loaded <collection>        # Show loaded segments
yami segment persistent <collection>    # Show persistent segments
yami segment stats <collection>         # Show segment statistics
```

### Alias Operations

```bash
yami alias list                         # List all aliases
yami alias list <collection>            # List aliases for a collection
yami alias describe <alias>             # Describe an alias
yami alias create <collection> <alias>  # Create an alias
yami alias drop <alias>                 # Drop an alias
yami alias alter <alias> <collection>   # Alter alias to new collection
```

### User/Role Management

```bash
yami user list                          # List users
yami user describe <name>               # Describe a user
yami user create <name> --password      # Create user
yami user drop <name>                   # Drop user
yami user update-password <name>        # Update password
yami user grant-role <user> <role>      # Grant role to user
yami user revoke-role <user> <role>     # Revoke role from user

yami role list                          # List roles
yami role describe <name>               # Describe a role
yami role create <name>                 # Create role
yami role drop <name>                   # Drop role
yami role grant <role> <priv> <obj>     # Grant privilege to role
yami role revoke <role> <priv> <obj>    # Revoke privilege from role
```

### Server Information

```bash
yami server version                     # Get server version
yami server type                        # Get server type (milvus/zilliz)
yami server info                        # Get all server information
```

## Output Formats

```bash
# Table output (default)
yami collection list

# JSON output
yami collection list -o json

# YAML output
yami collection list -o yaml
```

## Shell Completion

```bash
# Install completion for your shell
yami completion install

# Show completion script
yami completion show
```

## Environment Variables

- `MILVUS_URI` - Default Milvus server URI
- `MILVUS_TOKEN` - Default authentication token
- `YAMI_CONFIG_DIR` - Configuration directory (default: `~/.yami`)

## Requirements

- Python 3.10+
- Milvus 2.5+ (some features require 2.6+)

## License

Apache License 2.0
