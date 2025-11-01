#!/bin/bash

# Comprehensive test script for task_tool.py

VAULT_PATH="test_vault"

# Function to run a test and print the header
run_test() {
    echo ""
    echo "================================================="
    echo "TEST: $1"
    echo "================================================="
    python3 task_tool.py $VAULT_PATH query $2
}

# --- Basic Filter Tests ---
run_test "Query for all OPEN tasks" "--status open"
run_test "Query for all COMPLETED tasks" "--status completed"
run_test "Query for all CANCELLED tasks" "--status cancelled"

run_test "Query for HIGH priority tasks" "--priority high"
run_test "Query for MEDIUM priority tasks" "--priority medium"
run_test "Query for LOW priority tasks" "--priority low"

run_test "Query for OVERDUE tasks (due before 2025-10-20)" "--overdue"
run_test "Query for tasks DUE on 2025-10-20" "--due 2025-10-20"

# --- Tag Filter Tests ---
run_test "Query for tag #work/meetings" "--tag work/meetings"
run_test "Query for tag #personal/travel" "--tag personal/travel"
run_test "Query for a non-existent tag" "--tag non-existent-tag"

# --- Combination Filter Tests ---
run_test "Query for OPEN and HIGH priority tasks" "--status open --priority high"
run_test "Query for OVERDUE and tag #personal/finance" "--overdue --tag personal/finance"
run_test "Query for tasks with tag #work/reports and DUE on 2025-10-20" "--tag work/reports --due 2025-10-20"

# --- Verbose Flag Test ---
run_test "Query for OPEN tasks (VERBOSE)" "--status open --verbose"

# --- No Filter Test ---
run_test "Query with NO filters (should show all tasks)" ""

echo ""
echo "Test script finished."
