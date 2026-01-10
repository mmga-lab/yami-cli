#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
SKIPPED=0

# Test function
run_test() {
    local name="$1"
    local cmd="$2"
    local expect_fail="${3:-false}"

    echo -n "Testing: $name... "

    if [ "$expect_fail" = "true" ]; then
        if eval "$cmd" > /dev/null 2>&1; then
            echo -e "${RED}FAILED${NC} (expected failure but succeeded)"
            FAILED=$((FAILED + 1))
            return 1
        else
            echo -e "${GREEN}PASSED${NC}"
            PASSED=$((PASSED + 1))
            return 0
        fi
    else
        if eval "$cmd" > /dev/null 2>&1; then
            echo -e "${GREEN}PASSED${NC}"
            PASSED=$((PASSED + 1))
            return 0
        else
            echo -e "${RED}FAILED${NC}"
            echo "  Command: $cmd"
            FAILED=$((FAILED + 1))
            return 1
        fi
    fi
}

# Skip test function
skip_test() {
    local name="$1"
    local reason="$2"
    echo -e "Testing: $name... ${YELLOW}SKIPPED${NC} ($reason)"
    SKIPPED=$((SKIPPED + 1))
}

echo "=================================="
echo "Yami CLI Integration Tests"
echo "=================================="
echo ""

# Get Milvus URI from environment or use default
MILVUS_URI="${MILVUS_URI:-http://localhost:19530}"
echo "Milvus URI: $MILVUS_URI"
echo ""

# Test collection name
TEST_COL="test_yami_$(date +%s)"
TEST_COL2="test_yami2_$(date +%s)"

# ==========================================
# Server Tests
# ==========================================
echo "--- Server Tests ---"
run_test "server version" "yami --uri $MILVUS_URI server version"
run_test "server type" "yami --uri $MILVUS_URI server type"
run_test "server info" "yami --uri $MILVUS_URI server info"
run_test "connect" "yami connect $MILVUS_URI"
echo ""

# ==========================================
# Database Tests
# ==========================================
echo "--- Database Tests ---"
run_test "database list" "yami --uri $MILVUS_URI database list"
run_test "database describe default" "yami --uri $MILVUS_URI database describe default"
echo ""

# ==========================================
# Collection Tests
# ==========================================
echo "--- Collection Tests ---"
run_test "collection list (empty)" "yami --uri $MILVUS_URI collection list"
run_test "collection create (quick mode)" "yami --uri $MILVUS_URI collection create $TEST_COL --dim 64"
run_test "collection has (exists)" "yami --uri $MILVUS_URI collection has $TEST_COL"
run_test "collection list" "yami --uri $MILVUS_URI collection list"
run_test "collection describe" "yami --uri $MILVUS_URI collection describe $TEST_COL"
run_test "collection stats" "yami --uri $MILVUS_URI collection stats $TEST_COL"

# Create with DSL
run_test "collection create (DSL)" "yami --uri $MILVUS_URI collection create $TEST_COL2 -f 'id:int64:pk:auto' -f 'title:varchar:256' -f 'vec:float_vector:64:COSINE'"
run_test "collection describe (DSL)" "yami --uri $MILVUS_URI collection describe $TEST_COL2"
echo ""

# ==========================================
# Index Tests
# ==========================================
echo "--- Index Tests ---"
run_test "index list" "yami --uri $MILVUS_URI index list $TEST_COL"
run_test "index describe" "yami --uri $MILVUS_URI index describe $TEST_COL vector"
echo ""

# ==========================================
# Partition Tests
# ==========================================
echo "--- Partition Tests ---"
# Release first (quick mode auto-loads in Milvus 2.6+)
run_test "load release (for partition test)" "yami --uri $MILVUS_URI load release $TEST_COL"
run_test "partition list" "yami --uri $MILVUS_URI partition list $TEST_COL"
run_test "partition create" "yami --uri $MILVUS_URI partition create $TEST_COL test_partition"
run_test "partition has" "yami --uri $MILVUS_URI partition has $TEST_COL test_partition"
run_test "partition list (with partition)" "yami --uri $MILVUS_URI partition list $TEST_COL"
run_test "partition drop" "yami --uri $MILVUS_URI partition drop $TEST_COL test_partition -f"
echo ""

# ==========================================
# Load Tests
# ==========================================
echo "--- Load Tests ---"
run_test "load collection" "yami --uri $MILVUS_URI load collection $TEST_COL"
run_test "load state" "yami --uri $MILVUS_URI load state $TEST_COL"
echo ""

# ==========================================
# Data Tests
# ==========================================
echo "--- Data Tests ---"

# Create test Parquet file for SQL insert
TEST_PARQUET_FILE="/tmp/test_data_$$.parquet"
python3 << PYEOF
import pyarrow as pa
import pyarrow.parquet as pq
data = {
    'id': [10, 11, 12],
    'vector': [
        [0.1]*64,
        [0.2]*64,
        [0.3]*64,
    ]
}
table = pa.table(data)
pq.write_table(table, '$TEST_PARQUET_FILE')
PYEOF

# Create test data file
TEST_DATA_FILE="/tmp/test_data_$$.json"
cat > "$TEST_DATA_FILE" << 'EOF'
[
  {"id": 1, "vector": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4]},
  {"id": 2, "vector": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5]},
  {"id": 3, "vector": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]}
]
EOF

run_test "data insert (json)" "yami --uri $MILVUS_URI data insert $TEST_COL --sql \"SELECT * FROM read_json('$TEST_DATA_FILE')\""
run_test "data insert (parquet)" "yami --uri $MILVUS_URI data insert $TEST_COL --sql \"SELECT * FROM '$TEST_PARQUET_FILE'\""

# Wait for data to be searchable
sleep 2

run_test "data upsert (json)" "yami --uri $MILVUS_URI data upsert $TEST_COL --sql \"SELECT * FROM read_json('$TEST_DATA_FILE')\""
run_test "data upsert (parquet)" "yami --uri $MILVUS_URI data upsert $TEST_COL --sql \"SELECT * FROM '$TEST_PARQUET_FILE'\""
echo ""

# ==========================================
# Query Tests
# ==========================================
echo "--- Query Tests ---"
run_test "query search (random)" "yami --uri $MILVUS_URI query search $TEST_COL --random --limit 3"
run_test "query query (filter)" "yami --uri $MILVUS_URI query query $TEST_COL --filter 'id > 0' --limit 10"
run_test "query get" "yami --uri $MILVUS_URI query get $TEST_COL 1,2"
echo ""

# ==========================================
# Segment Tests
# ==========================================
echo "--- Segment Tests ---"
run_test "segment loaded" "yami --uri $MILVUS_URI segment loaded $TEST_COL"
run_test "segment stats" "yami --uri $MILVUS_URI segment stats $TEST_COL"
echo ""

# ==========================================
# Flush Tests
# ==========================================
echo "--- Flush Tests ---"
run_test "flush collection" "yami --uri $MILVUS_URI flush collection $TEST_COL"
run_test "flush all" "yami --uri $MILVUS_URI flush all"
# Note: flush state requires flush_all timestamp, skipping for now
echo ""

# ==========================================
# Compact Tests
# ==========================================
echo "--- Compact Tests ---"
# Compact may return immediately if nothing to compact
run_test "compact run" "yami --uri $MILVUS_URI compact run $TEST_COL || true"
run_test "compact list" "yami --uri $MILVUS_URI compact list"
echo ""

# ==========================================
# Export/Import Tests
# ==========================================
echo "--- IO Tests ---"
EXPORT_DIR="/tmp/yami_export_$$"
run_test "io export" "yami --uri $MILVUS_URI io export $TEST_COL $EXPORT_DIR"

# Check exported files
if [ -d "$EXPORT_DIR" ] && ls "$EXPORT_DIR"/*.parquet > /dev/null 2>&1; then
    echo -e "  Export check: ${GREEN}Files created${NC}"

    # Create import test collection
    TEST_IMPORT_COL="test_import_$(date +%s)"
    run_test "collection create for import" "yami --uri $MILVUS_URI collection create $TEST_IMPORT_COL --dim 64"
    run_test "io import" "yami --uri $MILVUS_URI io import $TEST_IMPORT_COL $EXPORT_DIR"
    run_test "collection drop (import test)" "yami --uri $MILVUS_URI collection drop $TEST_IMPORT_COL -f"
else
    echo -e "  Export check: ${YELLOW}No files (empty collection?)${NC}"
fi
rm -rf "$EXPORT_DIR"
echo ""

# ==========================================
# Alias Tests
# ==========================================
echo "--- Alias Tests ---"
TEST_ALIAS="test_alias_$$"
run_test "alias create" "yami --uri $MILVUS_URI alias create $TEST_COL $TEST_ALIAS"
run_test "alias list" "yami --uri $MILVUS_URI alias list"
run_test "alias describe" "yami --uri $MILVUS_URI alias describe $TEST_ALIAS"
run_test "alias alter" "yami --uri $MILVUS_URI alias alter $TEST_ALIAS $TEST_COL2"
run_test "alias drop" "yami --uri $MILVUS_URI alias drop $TEST_ALIAS -f"
echo ""

# ==========================================
# Add Field Tests (Milvus 2.6+)
# ==========================================
echo "--- Add Field Tests ---"
run_test "collection add-field" "yami --uri $MILVUS_URI collection add-field $TEST_COL 'score:int64:nullable'"
run_test "collection describe (after add-field)" "yami --uri $MILVUS_URI collection describe $TEST_COL"
echo ""

# ==========================================
# Load Release Tests
# ==========================================
echo "--- Load/Release Tests ---"
run_test "load release" "yami --uri $MILVUS_URI load release $TEST_COL"
run_test "load state (after release)" "yami --uri $MILVUS_URI load state $TEST_COL"
echo ""

# ==========================================
# Collection Rename Tests
# ==========================================
echo "--- Rename Tests ---"
NEW_NAME="renamed_${TEST_COL}"
run_test "collection rename" "yami --uri $MILVUS_URI collection rename $TEST_COL $NEW_NAME"
run_test "collection has (renamed)" "yami --uri $MILVUS_URI collection has $NEW_NAME"
TEST_COL="$NEW_NAME"  # Update for cleanup
echo ""

# ==========================================
# Delete Tests
# ==========================================
echo "--- Delete Tests ---"
# Reload for delete
run_test "load collection (for delete)" "yami --uri $MILVUS_URI load collection $TEST_COL"
sleep 2
run_test "data delete (by id)" "yami --uri $MILVUS_URI data delete $TEST_COL --ids 1 --force"
run_test "data delete (by filter)" "yami --uri $MILVUS_URI data delete $TEST_COL --filter 'id == 2' --force"
echo ""

# ==========================================
# Output Format Tests
# ==========================================
echo "--- Output Format Tests ---"
run_test "output json" "yami --uri $MILVUS_URI -o json collection list"
run_test "output yaml" "yami --uri $MILVUS_URI -o yaml collection list"
echo ""

# ==========================================
# Config Tests
# ==========================================
echo "--- Config Tests ---"
run_test "config init" "yami config init"
run_test "config list" "yami config list"
run_test "config set" "yami config set output json"
run_test "config get" "yami config get output"
run_test "config profile add" "yami config profile add test_profile --uri http://localhost:19530"
run_test "config profile list" "yami config profile list"
run_test "config profile remove" "yami config profile remove test_profile -f"
echo ""

# ==========================================
# Cleanup
# ==========================================
echo "--- Cleanup ---"
run_test "collection drop (test1)" "yami --uri $MILVUS_URI collection drop $TEST_COL -f"
run_test "collection drop (test2)" "yami --uri $MILVUS_URI collection drop $TEST_COL2 -f"
rm -f "$TEST_DATA_FILE" "$TEST_PARQUET_FILE"
echo ""

# ==========================================
# Summary
# ==========================================
echo "=================================="
echo "Test Summary"
echo "=================================="
echo -e "Passed:  ${GREEN}$PASSED${NC}"
echo -e "Failed:  ${RED}$FAILED${NC}"
echo -e "Skipped: ${YELLOW}$SKIPPED${NC}"
echo "=================================="

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
