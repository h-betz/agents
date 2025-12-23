# Zillow Lambda Deployment

## Structure
This Lambda function imports the shared `crawler` module from the parent project and loads session data from S3.

## Prerequisites

### 1. Upload Session Data to S3
```bash
# Create S3 bucket (if needed)
aws s3 mb s3://your-zillow-bucket

# Upload session data files
aws s3 cp crawler/session_data/ s3://your-zillow-bucket/session_data/ --recursive
```

### 2. IAM Role
Your Lambda needs an IAM role with these permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-zillow-bucket/session_data/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Deployment

### Option 1: Docker (Recommended)

Docker deployment uses AWS Lambda container images, which is easier to manage and supports larger dependencies.

```bash
# From project root
cd /path/to/bots

# Build the Docker image
docker build -t zillow-scraper -f aws/zillow/Dockerfile .

# Test locally (optional)
docker run -p 9000:8080 \
  -e ZILLOW_S3_BUCKET=your-zillow-bucket \
  zillow-scraper

# In another terminal, test the function
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'

# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker tag zillow-scraper:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/zillow-scraper:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/zillow-scraper:latest

# Create/Update Lambda function
aws lambda create-function \
  --function-name zillow-scraper \
  --package-type Image \
  --code ImageUri=YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/zillow-scraper:latest \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_ROLE \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables="{ZILLOW_S3_BUCKET=your-zillow-bucket}"
```

### Option 2: ZIP Package with dependencies
```bash
# From project root
cd aws/zillow
mkdir -p package

# Install dependencies
pip install -r requirements.txt -t package/

# Copy shared modules
cp -r ../../crawler package/
cp -r ../../utils package/ 2>/dev/null || true

# Create deployment package
cd package
zip -r ../zillow-lambda.zip .
cd ..
zip -g zillow-lambda.zip handler.py

# Deploy to AWS
aws lambda create-function \
  --function-name zillow-scraper \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_ROLE \
  --handler handler.lambda_handler \
  --zip-file fileb://zillow-lambda.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables="{ZILLOW_S3_BUCKET=your-zillow-bucket}"
```

## Environment Variables
Set these in Lambda configuration:
- `ZILLOW_S3_BUCKET` (required): S3 bucket containing session data files
- `ZILLOW_S3_PREFIX` (optional): S3 prefix/folder for session data (default: `session_data`)

## EventBridge Schedule
Set up an EventBridge rule to trigger on your desired schedule:
```bash
# Create a rule to run daily at 2 AM UTC
aws events put-rule \
  --name zillow-daily-scrape \
  --schedule-expression "cron(0 2 * * ? *)"

# Add Lambda as target
aws events put-targets \
  --rule zillow-daily-scrape \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:zillow-scraper"

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
  --function-name zillow-scraper \
  --statement-id EventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:REGION:ACCOUNT:rule/zillow-daily-scrape
```

## Local Testing
The code still works locally without S3:
```bash
# From project root
cd crawler
python zillow.py
```
