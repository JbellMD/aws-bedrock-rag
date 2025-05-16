import os
import boto3
import json
import logging
from typing import Dict, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

# Initialize the Bedrock client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

# The generative model ID to use
GENERATION_MODEL_ID = os.environ.get('GENERATION_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')


def generate_response(prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
    """
    Generate text response using Amazon Bedrock.
    
    Args:
        prompt (str): The input prompt to generate a response for
        max_tokens (int): Maximum number of tokens to generate
        temperature (float): Temperature for generation (0.0-1.0)
        
    Returns:
        str: The generated text response
    """
    try:
        logger.info(f"Generating response with model: {GENERATION_MODEL_ID}")
        
        # Anthropic Claude models use a specific format
        if GENERATION_MODEL_ID.startswith('anthropic.claude'):
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
        # Amazon Titan models use a different format
        elif GENERATION_MODEL_ID.startswith('amazon.titan'):
            request_body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9
                }
            }
        # AI21 Jurassic models use yet another format
        elif GENERATION_MODEL_ID.startswith('ai21'):
            request_body = {
                "prompt": prompt,
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": 0.9,
            }
        # Cohere models format
        elif GENERATION_MODEL_ID.startswith('cohere'):
            request_body = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        # Meta Llama models format
        elif GENERATION_MODEL_ID.startswith('meta.llama'):
            request_body = {
                "prompt": prompt,
                "max_gen_len": max_tokens,
                "temperature": temperature,
            }
        else:
            raise ValueError(f"Unsupported model: {GENERATION_MODEL_ID}")
        
        # Call the Bedrock generative model
        response = bedrock_runtime.invoke_model(
            modelId=GENERATION_MODEL_ID,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        
        # Extract the generated text from the response based on model type
        if GENERATION_MODEL_ID.startswith('anthropic.claude'):
            generated_text = response_body.get('content', [{}])[0].get('text', '')
        elif GENERATION_MODEL_ID.startswith('amazon.titan'):
            generated_text = response_body.get('results', [{}])[0].get('outputText', '')
        elif GENERATION_MODEL_ID.startswith('ai21'):
            generated_text = response_body.get('completions', [{}])[0].get('data', {}).get('text', '')
        elif GENERATION_MODEL_ID.startswith('cohere'):
            generated_text = response_body.get('generations', [{}])[0].get('text', '')
        elif GENERATION_MODEL_ID.startswith('meta.llama'):
            generated_text = response_body.get('generation', '')
        else:
            generated_text = "Unable to parse response from unsupported model"
        
        logger.info("Successfully generated response")
        return generated_text
    
    except Exception as e:
        logger.error(f"Error generating text response: {str(e)}")
        return f"Error generating response: {str(e)}"
