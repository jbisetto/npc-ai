"""
Integration tests for Bedrock model request formats.

These tests validate the request and response formats with real AWS Bedrock API calls.
They should only be run when AWS credentials are available and valid.
"""

import os
import json
import pytest
import logging
from pathlib import Path
from dotenv import load_dotenv
import boto3

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file in project root
project_root = Path(__file__).resolve().parent.parent.parent.parent
env_path = project_root / '.env'

if not env_path.exists():
    logger.warning(f".env file not found at {env_path}. These tests require AWS credentials.")

load_dotenv(dotenv_path=env_path)

# Test settings
TEST_PROMPT = "Hello! Can you help me with directions to Tokyo Station?"
CLAUDE_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
NOVA_MODEL_ID = "amazon.nova-micro-v1:0"
TITAN_MODEL_ID = "amazon.titan-text-express-v1"

# Skip these tests if AWS credentials are not available
requires_aws_credentials = pytest.mark.skipif(
    not (os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY')),
    reason="AWS credentials not available"
)

@pytest.fixture
def bedrock_client():
    """Create a boto3 Bedrock client for testing."""
    return boto3.client(
        'bedrock-runtime',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

@requires_aws_credentials
class TestBedrockFormats:
    """Integration tests for Bedrock model formats."""
    
    def test_nova_message_format(self, bedrock_client):
        """Test the Nova model with the message-based format."""
        # Skip if credentials are not set
        if not (os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY')):
            pytest.skip("AWS credentials not available")
        
        # Format for Nova models
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": TEST_PROMPT
                        }
                    ]
                }
            ]
        }
        
        logger.info(f"Testing Nova format: {json.dumps(request_body, indent=2)}")
        
        try:
            response = bedrock_client.invoke_model(
                modelId=NOVA_MODEL_ID,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            logger.info(f"Response Keys: {list(response_body.keys())}")
            
            # Verify the response format
            assert "output" in response_body
            assert "message" in response_body["output"]
            assert "content" in response_body["output"]["message"]
            assert len(response_body["output"]["message"]["content"]) > 0
            assert "text" in response_body["output"]["message"]["content"][0]
            
            # Log the response text
            response_text = response_body["output"]["message"]["content"][0]["text"]
            logger.info(f"Response text: {response_text[:100]}...")
            
        except Exception as e:
            logger.error(f"Error testing Nova format: {e}")
            pytest.fail(f"Error testing Nova format: {e}")
    
    @pytest.mark.skip(reason="Only run when testing Claude specifically")
    def test_claude_format(self, bedrock_client):
        """Test the Claude model with the anthropic message format."""
        # Skip if credentials are not set
        if not (os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY')):
            pytest.skip("AWS credentials not available")
        
        # Format for Claude models
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": TEST_PROMPT}
            ]
        }
        
        logger.info(f"Testing Claude format: {json.dumps(request_body, indent=2)}")
        
        try:
            response = bedrock_client.invoke_model(
                modelId=CLAUDE_MODEL_ID,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            logger.info(f"Response Keys: {list(response_body.keys())}")
            
            # Verify the response format
            assert "content" in response_body
            assert len(response_body["content"]) > 0
            assert "text" in response_body["content"][0]
            
            # Log the response text
            response_text = response_body["content"][0]["text"]
            logger.info(f"Response text: {response_text[:100]}...")
            
        except Exception as e:
            logger.error(f"Error testing Claude format: {e}")
            pytest.fail(f"Error testing Claude format: {e}")
    
    @pytest.mark.skip(reason="Only run when testing Titan specifically")
    def test_titan_format(self, bedrock_client):
        """Test the Titan model with the text generation format."""
        # Skip if credentials are not set
        if not (os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY')):
            pytest.skip("AWS credentials not available")
        
        # Format for Titan models
        request_body = {
            "inputText": TEST_PROMPT,
            "textGenerationConfig": {
                "maxTokenCount": 512,
                "stopSequences": [],
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        logger.info(f"Testing Titan format: {json.dumps(request_body, indent=2)}")
        
        try:
            response = bedrock_client.invoke_model(
                modelId=TITAN_MODEL_ID,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            logger.info(f"Response Keys: {list(response_body.keys())}")
            
            # Verify the response format
            assert "results" in response_body
            assert len(response_body["results"]) > 0
            assert "outputText" in response_body["results"][0]
            
            # Log the response text
            response_text = response_body["results"][0]["outputText"]
            logger.info(f"Response text: {response_text[:100]}...")
            
        except Exception as e:
            logger.error(f"Error testing Titan format: {e}")
            pytest.fail(f"Error testing Titan format: {e}") 