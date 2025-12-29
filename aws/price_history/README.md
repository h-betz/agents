# Price History Fetcher Lambda

This Lambda function fetches property price history from Zillow and stores it in the database. It's triggered by SQS messages containing zpid (Zillow Property ID).

## Architecture

```
Zillow Scraper Lambda → SQS Queue → Price History Lambda → Database
```

## Setup

### 1. Create SQS Queue

```bash
# Create the queue
aws sqs create-queue \
  --queue-name price-history-queue \
  --region us-east-2

# Get the queue URL
QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name price-history-queue \
  --region us-east-2 \
  --query 'QueueUrl' \
  --output text)

echo "Queue URL: $QUEUE_URL"
```

### 2. Deploy Lambda

```bash
./deploy.sh 352803440406 us-east-2 pirate-joes
```

### 3. Configure SQS Trigger

```bash
# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function \
  --function-name price-history-fetcher \
  --region us-east-2 \
  --query 'Configuration.FunctionArn' \
  --output text)

# Get Queue ARN
QUEUE_ARN=$(aws sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names QueueArn \
  --region us-east-2 \
  --query 'Attributes.QueueArn' \
  --output text)

# Add SQS as event source for Lambda
aws lambda create-event-source-mapping \
  --function-name price-history-fetcher \
  --event-source-arn $QUEUE_ARN \
  --batch-size 10 \
  --region us-east-2

# Grant Lambda permission to read from SQS
aws lambda add-permission \
  --function-name price-history-fetcher \
  --statement-id AllowSQSInvoke \
  --action lambda:InvokeFunction \
  --principal sqs.amazonaws.com \
  --source-arn $QUEUE_ARN \
  --region us-east-2
```

### 4. Set Environment Variables

Add these in the AWS Console or via CLI:

```bash
aws lambda update-function-configuration \
  --function-name price-history-fetcher \
  --environment "Variables={DB_HOST=your-db-host,DB_PORT=5432,DB_NAME=groceries,DB_USER=your-user,DB_PASSWORD=your-password,ZILLOW_S3_BUCKET=pirate-joes,ZILLOW_S3_PREFIX=crawler/session_data}" \
  --region us-east-2
```

**Required Environment Variables:**
- `DB_HOST` - Database hostname
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: groceries)
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `ZILLOW_S3_BUCKET` - S3 bucket containing Zillow session data (cookies)
- `ZILLOW_S3_PREFIX` - S3 prefix for session data files (default: crawler/session_data)

### 5. Update IAM Role

The Lambda needs SQS and S3 permissions. Add this policy to the Lambda's execution role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:us-east-2:352803440406:price-history-queue"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::pirate-joes/crawler/session_data/*"
    }
  ]
}
```

## Message Format

The Lambda expects SQS messages with this format:

```json
{
  "zpid": 38239866
}
```

## Testing

Send a test message to the queue:

```bash
aws sqs send-message \
  --queue-url $QUEUE_URL \
  --message-body '{"zpid": 38239866}' \
  --region us-east-2
```

Check CloudWatch Logs to see the results.

## Monitoring

- **CloudWatch Logs**: `/aws/lambda/price-history-fetcher`
- **SQS Metrics**: Monitor queue depth, age of oldest message
- **Lambda Metrics**: Monitor invocations, errors, duration
