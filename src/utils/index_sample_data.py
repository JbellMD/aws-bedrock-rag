import os
import sys
import json
import logging
import argparse
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.bedrock_embeddings import create_embeddings, batch_create_embeddings
from utils.opensearch_client import index_document, batch_index_documents

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_sample_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load sample data from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        List[Dict[str, Any]]: List of sample documents
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Successfully loaded {len(data)} documents from {file_path}")
        return data
    
    except Exception as e:
        logger.error(f"Error loading sample data: {str(e)}")
        return []


def index_data(documents: List[Dict[str, Any]], batch_size: int = 10) -> None:
    """
    Index sample data into OpenSearch.
    
    Args:
        documents (List[Dict[str, Any]]): List of documents to index
        batch_size (int): Number of documents to index in each batch
    """
    try:
        total_docs = len(documents)
        logger.info(f"Starting indexing of {total_docs} documents")
        
        # Process documents in batches
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_docs-1)//batch_size + 1} with {len(batch)} documents")
            
            # Create embeddings for the batch
            contents = [doc.get("content", "") for doc in batch]
            embeddings = batch_create_embeddings(contents)
            
            # Index the batch
            success = batch_index_documents(batch, embeddings)
            
            if success:
                logger.info(f"Successfully indexed batch {i//batch_size + 1}")
            else:
                logger.warning(f"Failed to index batch {i//batch_size + 1}")
        
        logger.info(f"Indexing complete for {total_docs} documents")
    
    except Exception as e:
        logger.error(f"Error indexing data: {str(e)}")


def create_sample_data() -> List[Dict[str, Any]]:
    """
    Create sample data for testing.
    
    Returns:
        List[Dict[str, Any]]: List of sample documents
    """
    return [
        {
            "id": "doc1",
            "content": "Amazon Bedrock is a fully managed service that offers a choice of high-performing foundation models (FMs) from leading AI companies like AI21 Labs, Anthropic, Cohere, Meta, Stability AI, and Amazon via a single API, along with a broad set of capabilities to build generative AI applications with security, privacy, and responsible AI.",
            "metadata": {"source": "sample", "category": "aws", "topic": "bedrock"}
        },
        {
            "id": "doc2",
            "content": "Amazon OpenSearch Service is a managed service that makes it easy to deploy, operate, and scale OpenSearch clusters in the AWS Cloud. OpenSearch is a fully open-source search and analytics engine for use cases such as log analytics, real-time application monitoring, and clickstream analysis.",
            "metadata": {"source": "sample", "category": "aws", "topic": "opensearch"}
        },
        {
            "id": "doc3",
            "content": "AWS Lambda is a serverless compute service that lets you run code without provisioning or managing servers, creating workload-aware cluster scaling logic, maintaining event integrations, or managing runtimes. With Lambda, you can run code for virtually any type of application or backend service - all with zero administration.",
            "metadata": {"source": "sample", "category": "aws", "topic": "lambda"}
        },
        {
            "id": "doc4",
            "content": "Amazon API Gateway is a fully managed service that makes it easy for developers to create, publish, maintain, monitor, and secure APIs at any scale. APIs act as the 'front door' for applications to access data, business logic, or functionality from your backend services.",
            "metadata": {"source": "sample", "category": "aws", "topic": "api-gateway"}
        },
        {
            "id": "doc5",
            "content": "Retrieval-Augmented Generation (RAG) is a technique used in natural language processing where an LLM retrieves facts from an external knowledge source to ground its responses in reliable, up-to-date information. This helps reduce hallucinations and provides source attribution.",
            "metadata": {"source": "sample", "category": "concept", "topic": "rag"}
        }
    ]


def save_sample_data(documents: List[Dict[str, Any]], file_path: str) -> None:
    """
    Save sample data to a JSON file.
    
    Args:
        documents (List[Dict[str, Any]]): List of documents to save
        file_path (str): Path to save the JSON file
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2)
        
        logger.info(f"Successfully saved {len(documents)} documents to {file_path}")
    
    except Exception as e:
        logger.error(f"Error saving sample data: {str(e)}")


def main():
    """
    Main function to run the sample data indexing utility.
    """
    parser = argparse.ArgumentParser(description='Index sample data into OpenSearch')
    parser.add_argument('--file', '-f', type=str, help='Path to sample data JSON file')
    parser.add_argument('--create', '-c', action='store_true', help='Create and save sample data')
    parser.add_argument('--output', '-o', type=str, default='sample_data.json', help='Output file for created sample data')
    parser.add_argument('--batch-size', '-b', type=int, default=10, help='Batch size for indexing')
    
    args = parser.parse_args()
    
    # Create and save sample data if requested
    if args.create:
        logger.info("Creating sample data")
        sample_data = create_sample_data()
        save_sample_data(sample_data, args.output)
        
        # Use the created data for indexing
        documents = sample_data
    
    # Load sample data from file if provided
    elif args.file:
        logger.info(f"Loading sample data from {args.file}")
        documents = load_sample_data(args.file)
    
    # Otherwise, use the default sample data
    else:
        logger.info("Using default sample data")
        documents = create_sample_data()
    
    # Index the documents
    if documents:
        index_data(documents, args.batch_size)
    else:
        logger.error("No documents to index")


if __name__ == "__main__":
    main()
