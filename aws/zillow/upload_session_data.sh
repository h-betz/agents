#!/bin/bash

# Helper script to upload session data to S3
# Usage: ./upload_session_data.sh <bucket-name>

if [ -z "$1" ]; then
    echo "Usage: $0 <s3-bucket-name>"
    echo "Example: $0 my-zillow-bucket"
    exit 1
fi

BUCKET=$1
SESSION_DATA_DIR="../../crawler/session_data"

echo "Uploading session data to s3://$BUCKET/session_data/"

if [ ! -d "$SESSION_DATA_DIR" ]; then
    echo "Error: Session data directory not found at $SESSION_DATA_DIR"
    exit 1
fi

aws s3 cp "$SESSION_DATA_DIR" "s3://$BUCKET/session_data/" --recursive

if [ $? -eq 0 ]; then
    echo "✓ Session data uploaded successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Set ZILLOW_S3_BUCKET=$BUCKET in your Lambda environment variables"
    echo "2. Deploy your Lambda function"
else
    echo "✗ Upload failed"
    exit 1
fi
