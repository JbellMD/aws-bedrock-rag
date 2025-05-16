import os
import json
import logging
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

# Import our utility modules
from utils.bedrock_embeddings import create_embeddings
from utils.bedrock_generation import generate_response
from utils.opensearch_client import search_vectors

# Setup logging
logger = Logger(service="bedrock-rag-service")

def lambda_handler(event: APIGatewayProxyEvent, context: LambdaContext):
    """
    Main Lambda handler function that processes API Gateway requests,
    generates embeddings, searches for context in OpenSearch,
    and returns AI-generated responses.
    """
    try:
        logger.info("Processing incoming request")
        
        # Parse the incoming request
        if isinstance(event.get('body'), str):
            body = json.loads(event.get('body', '{}'))
        else:
            body = event.get('body', {}) or {}
        
        user_prompt = body.get('prompt', '')
        if not user_prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No prompt provided'})
            }
        
        # Step 1: Convert the user prompt into embeddings
        logger.info("Generating embeddings for user prompt")
        embeddings = create_embeddings(user_prompt)
        
        # Step 2: Search for relevant context in OpenSearch
        logger.info("Searching for relevant context in OpenSearch")
        search_results = search_vectors(embeddings)
        
        # Step 3: Format retrieved context for prompt enrichment
        context = ""
        if search_results and len(search_results) > 0:
            context = "\n\n".join([result.get('content', '') for result in search_results])
            logger.info(f"Retrieved {len(search_results)} context items")
        
        # Step 4: Generate a response using Bedrock with the enriched context
        logger.info("Generating response with Bedrock")
        enriched_prompt = f"""
        You are a helpful assistant with access to the following information:
        
        {context}
        
        Based on this information, please answer the following question:
        {user_prompt}
        
        If the information provided doesn't contain the answer, please say so. Only use the information provided to construct your answer.
        """
        
        response = generate_response(enriched_prompt)
        
        # Step 5: Return the generated response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'response': response,
                'context_retrieved': bool(context)
            })
        }
        
    except Exception as e:
        logger.exception("Error processing request")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }
