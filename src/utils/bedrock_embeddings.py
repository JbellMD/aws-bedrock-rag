import os
import boto3
import json
import logging
from typing import List, Dict, Any

# Setup logging
logger = logging.getLogger(__name__)

# Initialize the Bedrock client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

# The embedding model ID to use
EMBEDDING_MODEL_ID = os.environ.get('EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v1')


def create_embeddings(text: str) -> List[float]:
    """
    Generate embeddings for the input text using Amazon Bedrock.
    
    Args:
        text (str): The input text to generate embeddings for
        
    Returns:
        List[float]: The generated embedding vector
    """
    try:
        logger.info(f"Creating embeddings with model: {EMBEDDING_MODEL_ID}")
        
        # Prepare the request body
        request_body = {
            "inputText": text
        }
        
        # Call the Bedrock embedding model
        response = bedrock_runtime.invoke_model(
            modelId=EMBEDDING_MODEL_ID,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        
        # Extract embeddings from the response
        embeddings = response_body.get('embedding', [])
        
        logger.info(f"Successfully generated embeddings with dimension: {len(embeddings)}")
        return embeddings
    
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        # Return empty list on error, which will be handled by the calling function
        return []


def batch_create_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts.
    
    Args:
        texts (List[str]): List of input texts to generate embeddings for
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    embeddings = []
    
    for text in texts:
        embedding = create_embeddings(text)
        embeddings.append(embedding)
    
    return embeddings
