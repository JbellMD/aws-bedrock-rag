# AWS Bedrock RAG Application

A serverless Retrieval-Augmented Generation (RAG) system built on AWS services including Lambda, API Gateway, Bedrock, and OpenSearch.

## Architecture Overview

This application implements a RAG pattern using the following AWS services:

1. **Amazon API Gateway**: Provides a RESTful API endpoint for user interactions
2. **AWS Lambda**: Processes input prompts and orchestrates the RAG workflow
3. **Amazon Bedrock**: 
   - Embedding Model: Converts text into vector embeddings
   - Generative Model: Produces AI responses with retrieved context
4. **Amazon OpenSearch**: Vector database for storing and retrieving document embeddings

## Project Structure

```
aws-bedrock-rag/
├── infrastructure/
│   └── cloudformation.yaml     # CloudFormation template for AWS resources
├── src/
│   ├── api/
│   │   └── api_gateway.py      # API Gateway configuration utilities
│   ├── lambda/
│   │   └── app.py              # Lambda function handler
│   ├── utils/
│   │   ├── bedrock_embeddings.py    # Utilities for creating embeddings
│   │   ├── bedrock_generation.py    # Utilities for text generation
│   │   ├── opensearch_client.py     # OpenSearch interaction utilities
│   │   └── index_sample_data.py     # Utility for indexing sample data
│   ├── test_locally.py         # Script for local testing
│   └── .env.sample             # Sample environment variables file
└── requirements.txt            # Python dependencies
```

## Prerequisites

- AWS Account with access to Bedrock, Lambda, API Gateway, and OpenSearch
- Python 3.9+ installed locally
- AWS CLI configured (for deployment)
- Boto3 with Bedrock support

## Setup and Deployment

### 1. Local Setup

```bash
# Clone the repository
git clone <repository-url>
cd aws-bedrock-rag

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create an environment file
cp src/.env.sample src/.env
# Edit src/.env to add your AWS credentials and configuration
```

### 2. Deploy to AWS

#### Option 1: Using the AWS Management Console

1. Create an S3 bucket for the Lambda deployment package
2. Zip the `src` directory and upload it to the S3 bucket
3. Use the CloudFormation template in `infrastructure/cloudformation.yaml` to deploy the infrastructure

#### Option 2: Using the AWS CLI

```bash
# Create a deployment bucket
aws s3 mb s3://bedrock-rag-deployment-$(aws sts get-caller-identity --query Account --output text)-$(aws configure get region)

# Package the application
cd src
zip -r ../lambda-package.zip ./*
cd ..

# Upload the package to S3
aws s3 cp lambda-package.zip s3://bedrock-rag-deployment-$(aws sts get-caller-identity --query Account --output text)-$(aws configure get region)/lambda-package.zip

# Deploy the CloudFormation stack
aws cloudformation create-stack \
  --stack-name bedrock-rag-stack \
  --template-body file://infrastructure/cloudformation.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters \
      ParameterKey=DeploymentPackage,ParameterValue=lambda-package.zip \
      ParameterKey=Environment,ParameterValue=dev
```

## Local Testing

For local testing, you have a few options:

### 1. Test the Lambda function locally

```bash
# Set up your .env file with AWS credentials
# Then run the test script with a sample prompt
python src/test_locally.py --prompt "What is Amazon Bedrock?"
```

### 2. Index sample data for testing

```bash
# Create and index sample data
python src/utils/index_sample_data.py --create --output sample_data.json

# Or use existing sample data
python src/utils/index_sample_data.py --file sample_data.json
```

## API Usage

Once deployed, the API can be accessed via the API Gateway endpoint:

```
POST https://<api-id>.execute-api.<region>.amazonaws.com/<stage>/rag
```

Request body:
```json
{
  "prompt": "What is Amazon Bedrock?"
}
```

Response:
```json
{
  "response": "Amazon Bedrock is a fully managed service that offers high-performing foundation models...",
  "context_retrieved": true
}
```

## Environment Variables

The application uses the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| AWS_REGION | AWS Region | us-east-1 |
| EMBEDDING_MODEL_ID | Bedrock embedding model ID | amazon.titan-embed-text-v1 |
| GENERATION_MODEL_ID | Bedrock generative model ID | anthropic.claude-3-sonnet-20240229-v1:0 |
| OPENSEARCH_ENDPOINT | OpenSearch domain endpoint | localhost |
| OPENSEARCH_PORT | OpenSearch port | 9200 |
| OPENSEARCH_INDEX | OpenSearch index name | rag-documents |
| MAX_SEARCH_RESULTS | Maximum search results to return | 3 |

## Security Considerations

- The application uses IAM roles and policies to control access to AWS services
- API Gateway can be configured with authentication and authorization mechanisms
- For production use, consider adding:
  - API key validation
  - OAuth or Cognito authentication
  - VPC endpoints for enhanced security
  - Request validation and throttling

## Extending the Application

### Adding Custom Data Sources

To add your own data for RAG:

1. Prepare your documents in the expected format:
```python
documents = [
    {
        "id": "unique_id",
        "content": "Document text content",
        "metadata": {"source": "...", "category": "..."}
    },
    # More documents...
]
```

2. Index them using the provided utilities:
```python
from utils.bedrock_embeddings import batch_create_embeddings
from utils.opensearch_client import batch_index_documents

embeddings = batch_create_embeddings([doc["content"] for doc in documents])
batch_index_documents(documents, embeddings)
```

### Adding Custom Preprocessing

You can extend `app.py` to add custom preprocessing for specific document types:

```python
def preprocess_document(document):
    # Add custom preprocessing logic
    return processed_text
```

## Troubleshooting

### Common Issues

1. **OpenSearch Connection Errors**:
   - Check your VPC settings and security groups
   - Ensure the Lambda function has permissions to access OpenSearch

2. **Bedrock Model Access**:
   - Ensure you have enabled the specific Bedrock models in your AWS account
   - Check IAM permissions for Bedrock access

3. **Embedding Dimension Mismatch**:
   - If you change embedding models, update the dimension in OpenSearch index configuration

### Logging

The application uses structured logging with different log levels. To adjust the log level:

- Set the `LOG_LEVEL` environment variable to `DEBUG`, `INFO`, `WARNING`, or `ERROR`

## License

[MIT License](LICENSE)
