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
yami collection create <name> --dim N   # Create a collection
yami collection drop <name>             # Drop a collection
yami collection has <name>              # Check if collection exists
yami collection rename <old> <new>      # Rename a collection
yami collection stats <name>            # Get collection statistics
```

### Index Operations

```bash
yami index list <collection>                    # List indexes
yami index describe <collection> <index>        # Describe an index
yami index create <collection> <field>          # Create an index
yami index drop <collection> <index>            # Drop an index
```

### Data Operations

```bash
yami data insert <collection> --file data.json  # Insert from file
yami data upsert <collection> --file data.json  # Upsert from file
yami data delete <collection> --ids 1,2,3       # Delete by IDs
yami data delete <collection> --filter "x > 10" # Delete by filter
```

### Query Operations

```bash
yami query search <collection> --vector "[...]" --limit 10
yami query query <collection> --filter "age > 20"
yami query get <collection> 1,2,3               # Get by IDs
```

### Database Operations

```bash
yami database list                      # List databases
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
```

### User/Role Management

```bash
yami user list                          # List users
yami user create <name> --password      # Create user
yami user grant-role <user> <role>      # Grant role to user

yami role list                          # List roles
yami role create <name>                 # Create role
yami role grant <role> <privilege>      # Grant privilege to role
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

## Environment Variables

- `MILVUS_URI` - Default Milvus server URI
- `MILVUS_TOKEN` - Default authentication token
- `YAMI_CONFIG_DIR` - Configuration directory (default: `~/.yami`)

## License

Apache License 2.0
