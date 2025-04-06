#!/bin/bash

# Set PYTHONPATH to include the src directory
export PYTHONPATH=/Users/joeyb-mini/GenAI/npc-ai

# Run all tests with coverage report
echo "Running all tests with coverage report..."

# Change directory to project root to ensure proper paths
cd "$(dirname "$0")/.." 

# Run pytest with proper test discovery
python3 -m pytest \
    src/tests/backend \
    -v \
    --cov=src \
    --cov-report=term-missing \
    --ignore=src/tests/integration

# Exit with the pytest exit code
exit $? 
