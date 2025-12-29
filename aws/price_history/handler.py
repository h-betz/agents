import os
import json
from price_history_fetcher import PriceHistoryFetcher


def lambda_handler(event, context):
    """
    AWS Lambda handler for fetching price history

    Triggered by SQS messages containing zpid

    Environment Variables:
        DB_HOST: Database host
        DB_PORT: Database port (default: 5432)
        DB_NAME: Database name
        DB_USER: Database user
        DB_PASSWORD: Database password
        ZILLOW_S3_BUCKET: S3 bucket containing session data (optional)
        ZILLOW_S3_PREFIX: S3 prefix for session data files (optional)

    Args:
        event: SQS event with Records containing zpid
        context: Lambda context object

    Returns:
        dict: Response with statusCode and processing summary
    """
    # Initialize fetcher with S3 configuration from environment
    s3_bucket = os.environ.get('ZILLOW_S3_BUCKET')
    s3_prefix = "session_data"
    fetcher = PriceHistoryFetcher(s3_bucket=s3_bucket, s3_prefix=s3_prefix)

    processed = 0
    failed = 0

    try:
        for record in event['Records']:
            try:
                # Parse message body
                body = json.loads(record['body'])
                zpid = body['zpid']

                # Fetch and save price history
                fetcher.fetch_and_save(zpid)
                processed += 1

            except Exception as e:
                print(f"Error processing zpid {zpid}: {str(e)}")
                failed += 1
                # Don't raise - continue processing other records

        return {
            'statusCode': 200 if failed == 0 else 207,
            'body': json.dumps({
                'message': f'Processed {processed} properties, {failed} failed',
                'processed': processed,
                'failed': failed
            })
        }

    except Exception as e:
        print(f'Error in lambda_handler: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
