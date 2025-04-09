"""
Tests for the BedrockClient class.

Tests the request formatting and response parsing for different model types.
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from src.ai.npc.hosted.bedrock_client import BedrockClient
from src.ai.npc.hosted.usage_tracker import UsageTracker

# Sample prompts and responses for testing
SAMPLE_PROMPT = "Hello! Can you help me with directions to Tokyo Station?"

CLAUDE_RESPONSE = {
    "content": [{"text": "This is a test response from Claude"}]
}

NOVA_RESPONSE = {
    "output": {
        "message": {
            "content": [
                {"text": "This is a test response from Nova"}
            ]
        }
    },
    "stopReason": "EOS",
    "usage": {
        "inputTokens": 10,
        "outputTokens": 20
    }
}

TITAN_RESPONSE = {
    "results": [
        {"outputText": "This is a test response from Titan"}
    ]
}

@pytest.fixture
def mock_client():
    """Create a mock boto3 client for testing."""
    client = MagicMock()
    # Setup invoke_model to return different responses based on model_id
    response = MagicMock()
    response.return_value = {"body": MagicMock()}
    client.invoke_model = response
    return client

@pytest.fixture
def bedrock_client(mock_client):
    """Create a BedrockClient with a mock boto3 client."""
    with patch("boto3.client", return_value=mock_client):
        client = BedrockClient(debug_mode=False)
        client.client = mock_client
        return client

class TestBedrockClient:
    """Tests for the BedrockClient class."""
    
    def test_claude_request_format(self, bedrock_client, mock_client):
        """Test that Claude models use the correct request format."""
        # Configure mock to return a successful response
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps(CLAUDE_RESPONSE)
        mock_client.invoke_model.return_value = {"body": mock_body}
        
        # Call generate with Claude model
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        bedrock_client.generate(SAMPLE_PROMPT, model_id=model_id)
        
        # Get the call arguments
        args, kwargs = mock_client.invoke_model.call_args
        
        # Verify the request format
        request_body = json.loads(kwargs["body"])
        assert "messages" in request_body
        assert len(request_body["messages"]) == 1
        assert request_body["messages"][0]["role"] == "user"
        assert request_body["messages"][0]["content"] == SAMPLE_PROMPT
        assert "anthropic_version" in request_body
    
    def test_nova_request_format(self, bedrock_client, mock_client):
        """Test that Nova models use the correct request format."""
        # Configure mock to return a successful response
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps(NOVA_RESPONSE)
        mock_client.invoke_model.return_value = {"body": mock_body}
        
        # Call generate with Nova model
        model_id = "amazon.nova-micro-v1:0"
        bedrock_client.generate(SAMPLE_PROMPT, model_id=model_id)
        
        # Get the call arguments
        args, kwargs = mock_client.invoke_model.call_args
        
        # Verify the request format
        request_body = json.loads(kwargs["body"])
        assert "messages" in request_body
        assert len(request_body["messages"]) == 1
        assert request_body["messages"][0]["role"] == "user"
        assert isinstance(request_body["messages"][0]["content"], list)
        assert "text" in request_body["messages"][0]["content"][0]
        assert request_body["messages"][0]["content"][0]["text"] == SAMPLE_PROMPT
    
    def test_claude_response_parsing(self, bedrock_client, mock_client):
        """Test parsing Claude model responses."""
        # Configure mock to return a Claude response
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps(CLAUDE_RESPONSE)
        mock_client.invoke_model.return_value = {"body": mock_body}
        
        # Call generate with Claude model
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        response = bedrock_client.generate(SAMPLE_PROMPT, model_id=model_id)
        
        # Verify the response parsing
        assert response == "This is a test response from Claude"
    
    def test_nova_response_parsing(self, bedrock_client, mock_client):
        """Test parsing Nova model responses."""
        # Configure mock to return a Nova response
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps(NOVA_RESPONSE)
        mock_client.invoke_model.return_value = {"body": mock_body}
        
        # Call generate with Nova model
        model_id = "amazon.nova-micro-v1:0"
        response = bedrock_client.generate(SAMPLE_PROMPT, model_id=model_id)
        
        # Verify the response parsing
        assert response == "This is a test response from Nova"
    
    def test_titan_response_parsing(self, bedrock_client, mock_client):
        """Test parsing Titan model responses."""
        # Configure mock to return a Titan response
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps(TITAN_RESPONSE)
        mock_client.invoke_model.return_value = {"body": mock_body}
        
        # Call generate with Titan model
        model_id = "amazon.titan-text-express-v1"
        response = bedrock_client.generate(SAMPLE_PROMPT, model_id=model_id)
        
        # Verify the response parsing
        assert response == "This is a test response from Titan"
    
    def test_debug_mode(self):
        """Test that debug mode returns simulated responses."""
        # Create client in debug mode
        client = BedrockClient(debug_mode=True)
        
        # Call generate
        response = client.generate(SAMPLE_PROMPT)
        
        # Verify that the response contains the expected debug text
        assert "<thinking>" in response
        assert "English:" in response
        assert "Japanese:" in response 