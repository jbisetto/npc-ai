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

echo "=== Testing NPC AI REST API ==="
echo

echo "1. Root Endpoint"
echo "----------------"
curl -s -X GET $BASE_URL/ | format_json
echo
sleep 1

echo "2. Health Check Endpoint"
echo "------------------------"
curl -s -X GET $BASE_URL/api/v1/health | format_json
echo
sleep 1

echo "3. Get All NPCs"
echo "---------------"
curl -s -X GET $BASE_URL/api/v1/npcs | format_json
echo
sleep 1

echo "4. Get Specific NPC (Yamada)"
echo "---------------------------"
curl -s -X GET $BASE_URL/api/v1/npcs/yamada | format_json
echo
sleep 1

echo "4.1. Get Valid NPC IDs"
echo "---------------------------"
curl -s -X GET $BASE_URL/api/v1/valid-npc-ids | format_json
echo
sleep 1

echo "5. Chat with Yamada (Station Attendant Osaka)"
echo "------------------"
curl -s -X POST \
  $BASE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, can you help me find the Yamanote Line?",
    "npc_id": "station_attendant_osaka",
    "player_id": "test_player_1"
  }' | format_json
echo
sleep 2

echo "6. Follow-up Chat with Yamada to Test Conversation Context"
echo "---------------------------------------------------------"
curl -s -X POST \
  $BASE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Thank you. Where can I buy tickets?",
    "npc_id": "station_attendant_osaka",
    "player_id": "test_player_1"
  }' | format_json
echo
sleep 2

echo "7. Chat with Hachiko (Bilingual Dog Companion)"
echo "--------------------------------------------"
curl -s -X POST \
  $BASE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello Hachiko! Could you teach me some basic Japanese phrases for traveling?",
    "npc_id": "companion_dog",
    "player_id": "test_player_2"
  }' | format_json
echo
sleep 2

echo "8. Follow-up with Hachiko in Japanese"
echo "-----------------------------------"
curl -s -X POST \
  $BASE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "ありがとう、ハチ公！東京タワーはどこですか？",
    "npc_id": "companion_dog",
    "player_id": "test_player_2"
  }' | format_json
echo
sleep 2

echo "9. Chat with Different NPC (Suzuki - Information Booth Attendant)"
echo "--------------------------------"
curl -s -X POST \
  $BASE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I am looking for information about Tokyo attractions.",
    "npc_id": "information_booth_attendant",
    "player_id": "test_player_1"
  }' | format_json
echo
sleep 2

echo "10. Clear Conversation History"
echo "---------------------------"
curl -s -X DELETE $BASE_URL/api/v1/conversations/test_player_1 | format_json
echo
sleep 1

echo "11. Test After Clearing Conversation (Should Not Have Context)"
echo "-----------------------------------------------------------"
curl -s -X POST \
  $BASE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you remind me about our previous conversation?",
    "npc_id": "station_attendant_osaka",
    "player_id": "test_player_1"
  }' | format_json
echo

echo "=== Test Complete ===" 