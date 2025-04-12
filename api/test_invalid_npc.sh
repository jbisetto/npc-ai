#!/bin/bash
# Test script for checking invalid NPC IDs

# Set the base URL
BASE_URL="http://localhost:8002"

# Check if jq is available, otherwise use a simple display function
if command -v jq &> /dev/null; then
    function format_json() {
        jq .
    }
else
    echo "jq not found, displaying raw JSON output"
    function format_json() {
        cat
    }
fi

echo "=== Testing NPC ID Validation ==="
echo

echo "1. Test with valid NPC ID (companion_dog)"
echo "-----------------------------------"
curl -s -X POST \
  $BASE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, who are you?",
    "npc_id": "companion_dog",
    "player_id": "test_player_1"
  }' | format_json
echo
echo

echo "2. Test with invalid NPC ID (nonexistent_npc)"
echo "-----------------------------------"
curl -s -X POST \
  $BASE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, who are you?",
    "npc_id": "nonexistent_npc",
    "player_id": "test_player_1"
  }' | format_json
echo
echo

echo "3. Test with invalid NPC ID (hachiko)"
echo "-----------------------------------"
curl -s -X POST \
  $BASE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, who are you?",
    "npc_id": "hachiko",
    "player_id": "test_player_1"
  }' | format_json
echo

echo "=== Test Complete ===" 