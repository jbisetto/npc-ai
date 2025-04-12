#!/bin/bash
# Test script for NPC AI REST API

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

# Generate timestamp and debug ID for tracking
TIMESTAMP=$(date +%s)
DEBUG_ID="debug_${TIMESTAMP}"

echo "=== Testing NPC AI REST API === DEBUG_ID: ${DEBUG_ID}"
echo

echo "1. ask dog who they are, player1"
echo "------------------"
curl -X POST $BASE_URL/api/v1/chat -H "Content-Type: application/json" -d '{
  "npc_id": "companion_dog",
  "player_id": "player1",
  "message": "hello, who are you? debug_id='$DEBUG_ID'_1",
  "session_id": "companion_dog_'$TIMESTAMP'"
}' | format_json
echo
sleep 2

echo "2. ask them again but for player2"
echo "------------------"
curl -X POST $BASE_URL/api/v1/chat -H "Content-Type: application/json" -d '{
  "npc_id": "companion_dog",
  "player_id": "player2",
  "message": "hello, who are you? debug_id='$DEBUG_ID'_2",
  "session_id": "companion_dog_'$TIMESTAMP'"
}' | format_json
echo
sleep 2

echo "3. Different question, same player1"
echo "------------------"
curl -X POST $BASE_URL/api/v1/chat -H "Content-Type: application/json" -d '{
  "npc_id": "companion_dog",
  "player_id": "player1",
  "message": "can you tell me about the Yamanote Line? debug_id='$DEBUG_ID'_3",
  "session_id": "companion_dog_'$TIMESTAMP'"
}' | format_json
echo
sleep 2

echo "4. Clear Conversation History"
echo "---------------------------"
curl -s -X DELETE $BASE_URL/api/v1/conversations/player1 | format_json
echo
sleep 1
curl -s -X DELETE $BASE_URL/api/v1/conversations/player2 | format_json
echo
sleep 1

echo "=== Test Complete ===" 