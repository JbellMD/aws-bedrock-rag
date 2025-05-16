import os
import sys
import json
import argparse
import logging
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Mock API Gateway event
def create_mock_event(prompt):
    return {
        "body": json.dumps({"prompt": prompt}),
        "headers": {
            "Content-Type": "application/json"
        },
        "httpMethod": "POST",
        "isBase64Encoded": False,
        "path": "/rag",
        "pathParameters": None,
        "queryStringParameters": None,
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "api-id",
            "domainName": "id.execute-api.us-east-1.amazonaws.com",
            "httpMethod": "POST",
            "identity": {
                "sourceIp": "127.0.0.1"
            },
            "path": "/rag",
            "stage": "dev"
        },
        "resource": "/rag",
        "stageVariables": None
    }

def main():
    parser = argparse.ArgumentParser(description='Test RAG application locally')
    parser.add_argument('--prompt', '-p', type=str, required=True, help='User prompt to test')
    parser.add_argument('--env-file', '-e', type=str, default='.env', help='Path to .env file')
    
    args = parser.parse_args()
    
    # Load environment variables from specified .env file
    if os.path.exists(args.env_file):
        load_dotenv(args.env_file)
        logger.info(f"Loaded environment variables from {args.env_file}")
    else:
        logger.warning(f"Environment file {args.env_file} not found, using default environment variables")
    
    # Import the Lambda handler
    try:
        from lambda_function.app import lambda_handler
        
        # Create a mock event
        event = create_mock_event(args.prompt)
        
        # Call the Lambda handler
        logger.info(f"Calling Lambda handler with prompt: {args.prompt}")
        response = lambda_handler(event, None)
        
        # Print the response
        print("\n" + "-" * 80)
        print("RAG Response:")
        print("-" * 80)
        
        if isinstance(response, dict) and 'body' in response:
            body = json.loads(response['body'])
            print(f"Status Code: {response['statusCode']}")
            
            if 'response' in body:
                print("\nGenerated Answer:")
                print(body['response'])
                
                print("\nContext Retrieved:", "Yes" if body.get('context_retrieved', False) else "No")
            else:
                print(f"Unexpected response format: {body}")
        else:
            print(f"Unexpected response: {response}")
        
        print("-" * 80)
        
    except Exception as e:
        logger.error(f"Error running the test: {str(e)}")
        raise

if __name__ == "__main__":
    main()
