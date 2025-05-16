import os
import json
import logging
from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSHTTP
from opensearchpy.helpers import bulk
import boto3

# Setup logging
logger = logging.getLogger(__name__)

# OpenSearch configuration from environment variables
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT', 'localhost')
OPENSEARCH_PORT = int(os.environ.get('OPENSEARCH_PORT', 9200))
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX', 'rag-documents')
OPENSEARCH_USE_SSL = os.environ.get('OPENSEARCH_USE_SSL', 'True').lower() == 'true'
OPENSEARCH_VERIFY_CERTS = os.environ.get('OPENSEARCH_VERIFY_CERTS', 'True').lower() == 'true'
USE_AWS_AUTH = os.environ.get('USE_AWS_AUTH', 'True').lower() == 'true'
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Number of results to return from the vector search
MAX_SEARCH_RESULTS = int(os.environ.get('MAX_SEARCH_RESULTS', 3))


def get_opensearch_client() -> OpenSearch:
    """
    Create and return an OpenSearch client.
    
    Returns:
        OpenSearch: The OpenSearch client instance
    """
    try:
        connection_params = {
            'hosts': [{'host': OPENSEARCH_ENDPOINT, 'port': OPENSEARCH_PORT}],
            'use_ssl': OPENSEARCH_USE_SSL,
            'verify_certs': OPENSEARCH_VERIFY_CERTS,
            'connection_class': RequestsHttpConnection
        }
        
        # If using AWS auth, set up the connection with IAM credentials
        if USE_AWS_AUTH:
            logger.info("Initializing OpenSearch client with AWS auth")
            credentials = boto3.Session().get_credentials()
            connection_params['http_auth'] = ('admin', 'admin')  # Replace with IAM auth
            connection_params['connection_class'] = AWSHTTP
            connection_params['region'] = AWS_REGION
        else:
            logger.info("Initializing OpenSearch client without AWS auth")
            # Add basic auth if needed
            if os.environ.get('OPENSEARCH_USERNAME') and os.environ.get('OPENSEARCH_PASSWORD'):
                connection_params['http_auth'] = (
                    os.environ.get('OPENSEARCH_USERNAME', ''),
                    os.environ.get('OPENSEARCH_PASSWORD', '')
                )
        
        # Create and return the client
        client = OpenSearch(**connection_params)
        logger.info("OpenSearch client initialized successfully")
        return client
    
    except Exception as e:
        logger.error(f"Error creating OpenSearch client: {str(e)}")
        # Return None on error, which will be handled by the calling function
        raise


def create_index_if_not_exists(client: OpenSearch, index_name: str) -> None:
    """
    Create an OpenSearch index if it doesn't already exist.
    
    Args:
        client (OpenSearch): The OpenSearch client
        index_name (str): The name of the index to create
    """
    try:
        if not client.indices.exists(index=index_name):
            logger.info(f"Creating index: {index_name}")
            
            # Define index settings with vector search capabilities
            index_settings = {
                "settings": {
                    "index": {
                        "number_of_shards": 2,
                        "number_of_replicas": 1,
                        "knn": True
                    }
                },
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "content": {"type": "text"},
                        "metadata": {"type": "object"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,  # Adjust based on your embedding model
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib"
                            }
                        }
                    }
                }
            }
            
            # Create the index
            client.indices.create(index=index_name, body=index_settings)
            logger.info(f"Successfully created index: {index_name}")
        else:
            logger.info(f"Index {index_name} already exists")
    
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise


def index_document(document: Dict[str, Any], embedding: List[float]) -> bool:
    """
    Index a document with its embedding in OpenSearch.
    
    Args:
        document (Dict[str, Any]): The document to index
        embedding (List[float]): The embedding vector for the document
        
    Returns:
        bool: True if indexing was successful, False otherwise
    """
    try:
        # Get the OpenSearch client
        client = get_opensearch_client()
        
        # Ensure the index exists
        create_index_if_not_exists(client, OPENSEARCH_INDEX)
        
        # Prepare the document with its embedding
        doc_with_embedding = {
            "id": document.get("id", ""),
            "content": document.get("content", ""),
            "metadata": document.get("metadata", {}),
            "embedding": embedding
        }
        
        # Index the document
        response = client.index(
            index=OPENSEARCH_INDEX,
            body=doc_with_embedding,
            id=document.get("id", None),
            refresh=True  # Immediate refresh for testing
        )
        
        logger.info(f"Successfully indexed document with ID: {response['_id']}")
        return True
    
    except Exception as e:
        logger.error(f"Error indexing document: {str(e)}")
        return False


def search_vectors(embedding: List[float], k: int = MAX_SEARCH_RESULTS) -> List[Dict[str, Any]]:
    """
    Search for similar documents in OpenSearch using vector similarity.
    
    Args:
        embedding (List[float]): The query embedding vector
        k (int): Maximum number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of matching documents
    """
    try:
        # Get the OpenSearch client
        client = get_opensearch_client()
        
        # Check if the index exists
        if not client.indices.exists(index=OPENSEARCH_INDEX):
            logger.warning(f"Index {OPENSEARCH_INDEX} does not exist")
            return []
        
        # Prepare the search query with vector similarity
        search_query = {
            "size": k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": embedding,
                        "k": k
                    }
                }
            },
            "_source": ["id", "content", "metadata"]
        }
        
        # Execute the search
        response = client.search(
            index=OPENSEARCH_INDEX,
            body=search_query
        )
        
        # Process and return the search results
        results = []
        for hit in response["hits"]["hits"]:
            results.append({
                "id": hit["_source"].get("id", ""),
                "content": hit["_source"].get("content", ""),
                "metadata": hit["_source"].get("metadata", {}),
                "score": hit["_score"]
            })
        
        logger.info(f"Search returned {len(results)} results")
        return results
    
    except Exception as e:
        logger.error(f"Error searching vectors: {str(e)}")
        return []


def batch_index_documents(documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
    """
    Batch index multiple documents with their embeddings.
    
    Args:
        documents (List[Dict[str, Any]]): List of documents to index
        embeddings (List[List[float]]): List of embedding vectors for the documents
        
    Returns:
        bool: True if indexing was successful, False otherwise
    """
    try:
        if len(documents) != len(embeddings):
            logger.error("Number of documents and embeddings do not match")
            return False
        
        # Get the OpenSearch client
        client = get_opensearch_client()
        
        # Ensure the index exists
        create_index_if_not_exists(client, OPENSEARCH_INDEX)
        
        # Prepare the bulk indexing actions
        actions = []
        for i, doc in enumerate(documents):
            actions.append({
                "_index": OPENSEARCH_INDEX,
                "_id": doc.get("id", None),
                "_source": {
                    "id": doc.get("id", ""),
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "embedding": embeddings[i]
                }
            })
        
        # Execute the bulk indexing
        success, failed = bulk(client, actions, refresh=True)
        
        logger.info(f"Bulk indexing completed. Success: {success}, Failed: {len(failed)}")
        return len(failed) == 0
    
    except Exception as e:
        logger.error(f"Error batch indexing documents: {str(e)}")
        return False
