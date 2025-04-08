#!/usr/bin/env python
"""
Test script for Amazon Bedrock Nova Micro model request format.
"""

import boto3
import json
import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Find and load the .env file from project root
project_root = Path(__file__).resolve().parent
env_path = project_root / '.env'
logger.info(f"Looking for .env file at: {env_path}")

if not env_path.exists():
    logger.error(f".env file not found at {env_path}")
    logger.info("Please create a .env file with AWS credentials in the project root")
    sys.exit(1)

load_dotenv(dotenv_path=env_path)
logger.info(f".env file loaded successfully")

# Get AWS credentials from environment variables
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Check if credentials are loaded
if not AWS_ACCESS_KEY_ID or AWS_ACCESS_KEY_ID == 'your_access_key_here':
    logger.error("AWS Access Key ID not found or using placeholder value")
    sys.exit(1)

if not AWS_SECRET_ACCESS_KEY or AWS_SECRET_ACCESS_KEY == 'your_secret_key_here':
    logger.error("AWS Secret Access Key not found or using placeholder value")
    sys.exit(1)

logger.info(f"AWS credentials found. Using region: {AWS_REGION}")

# Define the model ID
MODEL_ID = 'amazon.nova-micro-v1:0'

# Test prompt
TEST_PROMPT = "Hello! Can you help me with directions to Tokyo Station?"

def test_nova_format():
    """Test the Amazon Nova Micro model request format."""
    
    logger.info(f"Testing model: {MODEL_ID}")
    
    try:
        # Create boto3 client
        client = boto3.client(
            'bedrock-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Based on the error message, the model expects a "messages" format
        try:
            # Format 1: Message-based format with content as array
            logger.info("Trying message-based format with content as array...")
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
            
            logger.info(f"Request body: {json.dumps(request_body, indent=2)}")
            
            response = client.invoke_model(
                modelId=MODEL_ID,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            logger.info(f"Response Keys: {list(response_body.keys())}")
            logger.info(f"Success! Response: {json.dumps(response_body, indent=2)[:500]}...")
            
            # If we get a successful response, show the full result
            if "results" in response_body:
                results = response_body.get("results", [])
                if results:
                    output_text = results[0].get("outputText", "No output text")
                    logger.info(f"Generated text: {output_text}")
                else:
                    logger.warning("No results in response")
        except Exception as e:
            logger.error(f"Format 1 Error: {e}")
            
            # Format 2: Claude-like format with array content
            try:
                logger.info("\nTrying Claude-like format...")
                request_body = {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": TEST_PROMPT}
                            ]
                        }
                    ],
                    "anthropic_version": "bedrock-2023-05-31"
                }
                
                logger.info(f"Request body: {json.dumps(request_body, indent=2)}")
                
                response = client.invoke_model(
                    modelId=MODEL_ID,
                    contentType='application/json',
                    accept='application/json',
                    body=json.dumps(request_body)
                )
                
                response_body = json.loads(response['body'].read())
                logger.info(f"Response Keys: {list(response_body.keys())}")
                logger.info(f"Success! Response: {json.dumps(response_body, indent=2)[:500]}...")
            except Exception as e:
                logger.error(f"Format 2 Error: {e}")
                
                # Format 3: Simplest possible message format
                try:
                    logger.info("\nTrying simplest possible message format...")
                    request_body = {
                        "messages": [
                            {
                                "role": "user",
                                "content": TEST_PROMPT
                            }
                        ]
                    }
                    
                    logger.info(f"Request body: {json.dumps(request_body, indent=2)}")
                    
                    response = client.invoke_model(
                        modelId=MODEL_ID,
                        contentType='application/json',
                        accept='application/json',
                        body=json.dumps(request_body)
                    )
                    
                    response_body = json.loads(response['body'].read())
                    logger.info(f"Response Keys: {list(response_body.keys())}")
                    logger.info(f"Success! Response: {json.dumps(response_body, indent=2)[:500]}...")
                except Exception as e:
                    logger.error(f"Format 3 Error: {e}")
                    
                    # Format 4: Try with the correct specific configuration for Nova micro from official AWS examples
                    try:
                        logger.info("\nTrying with Nova specific configuration from AWS examples...")
                        request_body = {
                            "prompt": TEST_PROMPT,
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "max_tokens": 512
                        }
                        
                        logger.info(f"Request body: {json.dumps(request_body, indent=2)}")
                        
                        response = client.invoke_model(
                            modelId=MODEL_ID,
                            contentType='application/json',
                            accept='application/json',
                            body=json.dumps(request_body)
                        )
                        
                        response_body = json.loads(response['body'].read())
                        logger.info(f"Response Keys: {list(response_body.keys())}")
                        logger.info(f"Success! Response: {json.dumps(response_body, indent=2)[:500]}...")
                    except Exception as e:
                        logger.error(f"Format 4 Error: {e}")
                        logger.error("All formats failed. Check model documentation or contact AWS support.")
            
    except Exception as e:
        logger.error(f"Overall test error: {e}")

if __name__ == "__main__":
    logger.info("Starting Bedrock Nova format test")
    test_nova_format()
    logger.info("Test completed") 