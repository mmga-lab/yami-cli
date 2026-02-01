# Yami CLI Troubleshooting Guide

Quick reference for diagnosing and resolving common issues.

## Quick Diagnostics

Run the built-in diagnostics tool first:

```bash
yami doctor
```

This checks:
- Yami, Python, and pymilvus versions
- Configuration files
- Profile settings
- Server connectivity

## Connection Issues

### Connection Refused

**Error**: `[E001] Connection Failed - Cannot connect to Milvus at http://localhost:19530`

**Causes**:
- Milvus server is not running
- Wrong URI or port

**Solutions**:
```bash
# Check if Milvus is running
docker ps | grep milvus

# Start Milvus (Docker)
docker compose up -d

# Verify connectivity
curl http://localhost:19530/healthz
```

### Connection Timeout

**Error**: `[E002] Connection Timeout`

**Causes**:
- Network latency
- Server under heavy load
- Firewall blocking connection

**Solutions**:
```bash
# Increase timeout
yami --timeout 60 collection list

# Check network
ping <milvus-host>

# Test port connectivity
nc -zv <host> 19530
```

### Authentication Failed

**Error**: `[E003] Authentication Failed`

**Causes**:
- Invalid or expired token
- Incorrect token format
- Missing authentication

**Solutions**:
```bash
# Check token is set
echo $MILVUS_TOKEN

# Update profile with new token
yami config profile add prod --uri https://xxx.com --token $TOKEN

# Verify token format
# For Zilliz Cloud: use API key directly
# For self-hosted: use "user:password" format
```

## Configuration Issues

### Profile Not Found

**Error**: `[E010] Profile Not Found`

**Causes**:
- Profile name misspelled
- Profile never created

**Solutions**:
```bash
# List available profiles
yami config profile list

# Create a new profile
yami config profile add local --uri http://localhost:19530

# Set as default
yami config profile use local
```

### Config File Errors

**Error**: `[E011] Invalid Configuration`

**Causes**:
- TOML syntax error
- Corrupted config file

**Solutions**:
```bash
# View config file
cat ~/.yami/config.toml

# Reinitialize config
yami config init

# Manually edit config
vim ~/.yami/config.toml
```

## Collection Issues

### Collection Not Found

**Error**: `[E020] Collection Not Found`

**Causes**:
- Collection name misspelled
- Collection dropped
- Wrong database

**Solutions**:
```bash
# List all collections
yami collection list

# Check in specific database
yami --db mydb collection list

# Verify collection exists
yami collection has my_collection
```

### Vector Dimension Mismatch

**Error**: `[E023] Vector Dimension Mismatch`

**Causes**:
- Input vector size differs from schema
- Wrong embedding model

**Solutions**:
```bash
# Check collection schema
yami collection describe my_collection

# Verify vector field dimension
# Ensure your embedding model outputs the correct dimension
```

## Data Issues

### Import Failures

**Causes**:
- File format incorrect
- Missing required fields
- Type mismatch

**Solutions**:
```bash
# Check collection schema
yami collection describe my_collection

# Validate Parquet/JSON file
# Ensure all required fields are present
# Ensure types match schema
```

### Duplicate Primary Key

**Error**: `[E032] Duplicate Primary Key`

**Causes**:
- Inserting existing IDs
- Duplicate IDs in input

**Solutions**:
```bash
# Use upsert instead of insert
yami data upsert my_collection --sql "SELECT * FROM 'data.parquet'"

# Remove duplicates from input
yami data insert my_collection --sql "SELECT DISTINCT * FROM 'data.parquet'"
```

## Debug Mode

For detailed troubleshooting, enable debug mode:

```bash
yami --debug collection list
```

This shows:
- Connection details
- pymilvus API calls
- Request/response data

## Environment Variables

Configure via environment:

```bash
export MILVUS_URI=http://localhost:19530
export MILVUS_TOKEN=your_token
export YAMI_CONFIG_DIR=~/.yami
export YAMI_MODE=human  # or 'agent' for JSON output
```

## Getting Help

- **Documentation**: https://github.com/mmga-lab/yami-cli
- **Issues**: https://github.com/mmga-lab/yami-cli/issues
- **Run diagnostics**: `yami doctor`

## Error Code Reference

| Code | Category | Description |
|------|----------|-------------|
| E001 | Connection | Connection failed |
| E002 | Connection | Connection timeout |
| E003 | Connection | Authentication failed |
| E004 | Connection | Server unreachable |
| E010 | Config | Profile not found |
| E011 | Config | Invalid configuration |
| E012 | Config | Configuration missing |
| E020 | Schema | Collection not found |
| E021 | Schema | Invalid schema |
| E022 | Schema | Field not found |
| E023 | Schema | Vector dimension mismatch |
| E030 | Data | Invalid data |
| E031 | Data | Data type mismatch |
| E032 | Data | Duplicate primary key |
| E040 | Operation | Operation failed |
| E041 | Operation | Permission denied |
| E042 | Operation | Resource not loaded |
| E099 | General | Unknown error |
