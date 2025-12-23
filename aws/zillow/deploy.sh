#!/bin/bash

# AWS Lambda Docker Deployment Script
# Usage: ./deploy.sh <aws-account-id> <region> <s3-bucket>

set -e

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <aws-account-id> <region> <s3-bucket> [function-name]"
    echo "Example: $0 123456789012 us-east-1 my-zillow-bucket zillow-scraper"
    exit 1
fi

ACCOUNT_ID=$1
REGION=$2
S3_BUCKET=$3
FUNCTION_NAME=${4:-zillow-scraper}
IMAGE_NAME="zillow-scraper"
ECR_REPO="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$IMAGE_NAME"

echo "========================================="
echo "Deploying Zillow Lambda Function"
echo "========================================="
echo "Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
echo "S3 Bucket: $S3_BUCKET"
echo "Function Name: $FUNCTION_NAME"
echo "========================================="

# Navigate to aws/zillow directory
cd "$(dirname "$0")"
echo "Building from: $(pwd)"

# Build Docker image (context is current directory)
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Create ECR repository if it doesn't exist
echo "Checking ECR repository..."
aws ecr describe-repositories --repository-names $IMAGE_NAME --region $REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $IMAGE_NAME --region $REGION

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin $ECR_REPO

# Tag and push image
echo "Pushing image to ECR..."
docker tag $IMAGE_NAME:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

# Check if function exists
echo "Checking if Lambda function exists..."
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --image-uri $ECR_REPO:latest \
        --region $REGION

    echo "Waiting for function update to complete..."
    aws lambda wait function-updated \
        --function-name $FUNCTION_NAME \
        --region $REGION

    # Get existing environment variables and merge with new ones
    echo "Preserving existing environment variables..."
    EXISTING_VARS=$(aws lambda get-function-configuration \
        --function-name $FUNCTION_NAME \
        --region $REGION \
        --query 'Environment.Variables' \
        --output json)

    # Merge existing vars with ZILLOW_S3_BUCKET using jq
    MERGED_VARS=$(echo $EXISTING_VARS | jq --arg bucket "$S3_BUCKET" '. + {ZILLOW_S3_BUCKET: $bucket}')

    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment "Variables=$MERGED_VARS" \
        --region $REGION
else
    echo "Creating new Lambda function..."
    echo "Note: You need to provide an IAM role ARN"
    read -p "Enter Lambda IAM Role ARN: " ROLE_ARN

    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --package-type Image \
        --code ImageUri=$ECR_REPO:latest \
        --role $ROLE_ARN \
        --timeout 300 \
        --memory-size 512 \
        --environment "Variables={ZILLOW_S3_BUCKET=$S3_BUCKET}" \
        --region $REGION
fi

echo "========================================="
echo "✓ Deployment complete!"
echo "========================================="
echo "Function: $FUNCTION_NAME"
echo "Image: $ECR_REPO:latest"
echo "Region: $REGION"
echo ""
echo "Test the function:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --region $REGION response.json"
