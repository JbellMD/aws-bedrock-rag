import boto3
import json
import os
import logging
from typing import Dict, Any

# Setup logging
logger = logging.getLogger(__name__)

# AWS region
region = os.environ.get('AWS_REGION', 'us-east-1')

# API Gateway client
api_gateway = boto3.client('apigateway', region_name=region)


def create_rest_api(api_name: str, description: str) -> Dict[str, Any]:
    """
    Create a new REST API in API Gateway.
    
    Args:
        api_name (str): The name of the API
        description (str): A description of the API
        
    Returns:
        Dict[str, Any]: The API Gateway response
    """
    try:
        response = api_gateway.create_rest_api(
            name=api_name,
            description=description,
            endpointConfiguration={
                'types': ['REGIONAL']
            },
            apiKeySource='HEADER',
            disableExecuteApiEndpoint=False
        )
        
        logger.info(f"Successfully created API: {api_name}")
        return response
    
    except Exception as e:
        logger.error(f"Error creating REST API: {str(e)}")
        raise


def create_resource(api_id: str, parent_id: str, path_part: str) -> Dict[str, Any]:
    """
    Create a new resource in an API Gateway API.
    
    Args:
        api_id (str): The ID of the API
        parent_id (str): The ID of the parent resource
        path_part (str): The path part for the resource
        
    Returns:
        Dict[str, Any]: The API Gateway response
    """
    try:
        response = api_gateway.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        
        logger.info(f"Successfully created resource: {path_part}")
        return response
    
    except Exception as e:
        logger.error(f"Error creating resource: {str(e)}")
        raise


def create_method(api_id: str, resource_id: str, http_method: str, 
                 authorization_type: str = 'NONE') -> Dict[str, Any]:
    """
    Create a new method for a resource in an API Gateway API.
    
    Args:
        api_id (str): The ID of the API
        resource_id (str): The ID of the resource
        http_method (str): The HTTP method (GET, POST, etc.)
        authorization_type (str): The authorization type for the method
        
    Returns:
        Dict[str, Any]: The API Gateway response
    """
    try:
        response = api_gateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            authorizationType=authorization_type,
            apiKeyRequired=False
        )
        
        logger.info(f"Successfully created method: {http_method}")
        return response
    
    except Exception as e:
        logger.error(f"Error creating method: {str(e)}")
        raise


def create_integration(api_id: str, resource_id: str, http_method: str, 
                      lambda_function_arn: str) -> Dict[str, Any]:
    """
    Create a Lambda integration for a method in an API Gateway API.
    
    Args:
        api_id (str): The ID of the API
        resource_id (str): The ID of the resource
        http_method (str): The HTTP method (GET, POST, etc.)
        lambda_function_arn (str): The ARN of the Lambda function
        
    Returns:
        Dict[str, Any]: The API Gateway response
    """
    try:
        response = api_gateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_function_arn}/invocations',
            passthroughBehavior='WHEN_NO_MATCH',
            contentHandling='CONVERT_TO_TEXT',
            timeoutInMillis=29000
        )
        
        logger.info(f"Successfully created integration for method: {http_method}")
        return response
    
    except Exception as e:
        logger.error(f"Error creating integration: {str(e)}")
        raise


def create_method_response(api_id: str, resource_id: str, 
                         http_method: str, status_code: str) -> Dict[str, Any]:
    """
    Create a method response for a method in an API Gateway API.
    
    Args:
        api_id (str): The ID of the API
        resource_id (str): The ID of the resource
        http_method (str): The HTTP method (GET, POST, etc.)
        status_code (str): The HTTP status code
        
    Returns:
        Dict[str, Any]: The API Gateway response
    """
    try:
        response = api_gateway.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode=status_code,
            responseModels={
                'application/json': 'Empty'
            },
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': True,
                'method.response.header.Access-Control-Allow-Methods': True,
                'method.response.header.Access-Control-Allow-Headers': True
            }
        )
        
        logger.info(f"Successfully created method response with status code: {status_code}")
        return response
    
    except Exception as e:
        logger.error(f"Error creating method response: {str(e)}")
        raise


def create_integration_response(api_id: str, resource_id: str, 
                              http_method: str, status_code: str) -> Dict[str, Any]:
    """
    Create an integration response for a method in an API Gateway API.
    
    Args:
        api_id (str): The ID of the API
        resource_id (str): The ID of the resource
        http_method (str): The HTTP method (GET, POST, etc.)
        status_code (str): The HTTP status code
        
    Returns:
        Dict[str, Any]: The API Gateway response
    """
    try:
        response = api_gateway.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode=status_code,
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': "'*'",
                'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'",
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
            },
            responseTemplates={
                'application/json': ''
            }
        )
        
        logger.info(f"Successfully created integration response with status code: {status_code}")
        return response
    
    except Exception as e:
        logger.error(f"Error creating integration response: {str(e)}")
        raise


def deploy_api(api_id: str, stage_name: str, stage_description: str) -> Dict[str, Any]:
    """
    Deploy an API Gateway API to a stage.
    
    Args:
        api_id (str): The ID of the API
        stage_name (str): The name of the stage
        stage_description (str): A description of the stage
        
    Returns:
        Dict[str, Any]: The API Gateway response
    """
    try:
        response = api_gateway.create_deployment(
            restApiId=api_id,
            stageName=stage_name,
            stageDescription=stage_description,
            description=f'Deployment to {stage_name} stage'
        )
        
        logger.info(f"Successfully deployed API to stage: {stage_name}")
        return response
    
    except Exception as e:
        logger.error(f"Error deploying API: {str(e)}")
        raise


def update_cors_for_resource(api_id: str, resource_id: str) -> None:
    """
    Set up CORS for a resource in an API Gateway API.
    
    Args:
        api_id (str): The ID of the API
        resource_id (str): The ID of the resource
    """
    try:
        # Create OPTIONS method
        create_method(api_id, resource_id, 'OPTIONS', 'NONE')
        
        # Create mock integration for OPTIONS method
        api_gateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            integrationHttpMethod='OPTIONS',
            passthroughBehavior='WHEN_NO_MATCH',
            requestTemplates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        # Create method response for OPTIONS method
        create_method_response(api_id, resource_id, 'OPTIONS', '200')
        
        # Create integration response for OPTIONS method
        create_integration_response(api_id, resource_id, 'OPTIONS', '200')
        
        logger.info(f"Successfully updated CORS for resource")
    
    except Exception as e:
        logger.error(f"Error updating CORS for resource: {str(e)}")
        raise


def setup_api_gateway(api_name: str, description: str, lambda_function_arn: str) -> str:
    """
    Set up a complete API Gateway for the RAG application.
    
    Args:
        api_name (str): The name of the API
        description (str): A description of the API
        lambda_function_arn (str): The ARN of the Lambda function
        
    Returns:
        str: The API Gateway invoke URL
    """
    try:
        # Create the API
        api = create_rest_api(api_name, description)
        api_id = api['id']
        
        # Get the root resource ID
        resources = api_gateway.get_resources(restApiId=api_id)
        root_id = None
        for resource in resources['items']:
            if resource['path'] == '/':
                root_id = resource['id']
                break
        
        # Create a resource for the RAG endpoint
        rag_resource = create_resource(api_id, root_id, 'rag')
        rag_resource_id = rag_resource['id']
        
        # Create a POST method for the RAG endpoint
        create_method(api_id, rag_resource_id, 'POST', 'NONE')
        
        # Create a Lambda integration for the POST method
        create_integration(api_id, rag_resource_id, 'POST', lambda_function_arn)
        
        # Create a method response for the POST method
        create_method_response(api_id, rag_resource_id, 'POST', '200')
        
        # Create an integration response for the POST method
        create_integration_response(api_id, rag_resource_id, 'POST', '200')
        
        # Update CORS for the RAG endpoint
        update_cors_for_resource(api_id, rag_resource_id)
        
        # Deploy the API to a stage
        deploy_api(api_id, 'prod', 'Production stage')
        
        # Construct the invoke URL
        invoke_url = f'https://{api_id}.execute-api.{region}.amazonaws.com/prod/rag'
        
        logger.info(f"API Gateway setup complete. Invoke URL: {invoke_url}")
        return invoke_url
    
    except Exception as e:
        logger.error(f"Error setting up API Gateway: {str(e)}")
        raise
