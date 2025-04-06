"""
Log filter for redacting sensitive information in logs.

This module provides filters for logging that redact sensitive information
like AWS credentials, API keys, and other secrets.
"""

import logging
import re
import json

class SensitiveInfoFilter(logging.Filter):
    """
    A logging filter that redacts sensitive information from log records.
    
    This filter searches for common patterns of sensitive information like
    AWS credentials, API keys, and other secrets, and replaces them with
    a redacted placeholder.
    """
    
    def __init__(self):
        super().__init__()
        
        # Patterns for sensitive information
        self.patterns = [
            # AWS credentials in Authorization headers
            (re.compile(r'(Credential=)([A-Z0-9]+)(/)', re.IGNORECASE), r'\1[REDACTED]\3'),
            # Signatures
            (re.compile(r'(Signature=)([a-f0-9]+)', re.IGNORECASE), r'\1[REDACTED]'),
            # API keys and tokens
            (re.compile(r'(api[-_]key|token|auth|secret|password)(["\s:]*)([^"\s,}{]+)', re.IGNORECASE), r'\1\2[REDACTED]'),
            # Bearer tokens
            (re.compile(r'(Bearer\s+)([A-Za-z0-9-._~+/]+)', re.IGNORECASE), r'\1[REDACTED]'),
            # AWS Access Key ID pattern
            (re.compile(r'(AKIA|ASIA)[A-Z0-9]{16}'), '[REDACTED-ACCESS-KEY]'),
            # Other common authentication headers
            (re.compile(r'(Authorization|Authentication|X-Api-Key)(:?\s+)([^\s]+)'), r'\1\2[REDACTED]'),
            # URLs with credentials
            (re.compile(r'(https?://)[^:@\s]+:[^@\s]+(@)', re.IGNORECASE), r'\1[REDACTED]\2'),
        ]
    
    def filter(self, record):
        """
        Filter log records to redact sensitive information.
        
        Args:
            record: The log record to filter
            
        Returns:
            True to include the record in log output, False to exclude it
        """
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Apply each pattern to the message
            for pattern, replacement in self.patterns:
                record.msg = pattern.sub(replacement, record.msg)
                
            # Special handling for JSON content
            if '{' in record.msg and '}' in record.msg:
                try:
                    # Try to find and parse JSON in the message
                    start = record.msg.find('{')
                    end = record.msg.rfind('}') + 1
                    if start < end:
                        json_str = record.msg[start:end]
                        # Only try to parse if it looks like valid JSON
                        if ('"' in json_str or "'" in json_str) and (':' in json_str or '=' in json_str):
                            json_obj = json.loads(json_str)
                            # Redact known sensitive fields
                            self._redact_json(json_obj)
                            # Replace the JSON portion of the message
                            redacted_json = json.dumps(json_obj, indent=2)
                            record.msg = record.msg[:start] + redacted_json + record.msg[end:]
                except (ValueError, json.JSONDecodeError):
                    # If JSON parsing fails, continue with regex-based redaction
                    pass
                    
        # If args contain strings, redact those as well
        if hasattr(record, 'args') and isinstance(record.args, tuple):
            args_list = list(record.args)
            for i, arg in enumerate(args_list):
                if isinstance(arg, str):
                    for pattern, replacement in self.patterns:
                        args_list[i] = pattern.sub(replacement, arg)
            record.args = tuple(args_list)
            
        return True
    
    def _redact_json(self, json_obj):
        """
        Recursively redact sensitive fields in a JSON object.
        
        Args:
            json_obj: The JSON object to redact
        """
        if not isinstance(json_obj, (dict, list)):
            return
            
        sensitive_keys = [
            "credential", "credentials", "access_key", "secret_key", 
            "password", "token", "authorization", "auth", "api_key",
            "secret", "signature", "key"
        ]
        
        if isinstance(json_obj, dict):
            for key in list(json_obj.keys()):
                if isinstance(json_obj[key], (dict, list)):
                    self._redact_json(json_obj[key])
                elif any(s in key.lower() for s in sensitive_keys):
                    json_obj[key] = "[REDACTED]"
        elif isinstance(json_obj, list):
            for i, item in enumerate(json_obj):
                if isinstance(item, (dict, list)):
                    self._redact_json(item)

def install_sensitive_data_filter():
    """
    Install the sensitive information filter on all loggers.
    
    This function adds the SensitiveInfoFilter to the root logger
    and key loggers that might contain sensitive information.
    """
    sensitive_filter = SensitiveInfoFilter()
    
    # Add to root logger to catch all logs
    root_logger = logging.getLogger()
    root_logger.addFilter(sensitive_filter)
    
    # Add specifically to AWS SDK loggers
    aws_loggers = [
        logging.getLogger('boto3'),
        logging.getLogger('botocore'),
        logging.getLogger('s3transfer'),
        logging.getLogger('urllib3'),
        logging.getLogger('requests'),
        logging.getLogger('src.ai.companion.hosted.bedrock_client')
    ]
    
    for logger in aws_loggers:
        logger.addFilter(sensitive_filter)
        
    # Also add to handlers of the root logger
    for handler in root_logger.handlers:
        handler.addFilter(sensitive_filter) 