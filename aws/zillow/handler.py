import os
import json

from zillow import Zillow


def lambda_handler(event, context):
    """
    AWS Lambda handler for Zillow scraper

    Environment Variables:
        ZILLOW_S3_BUCKET: S3 bucket containing session data (required)
        ZILLOW_S3_PREFIX: S3 prefix/folder for session data (default: session_data)

    Args:
        event: Lambda event object
        context: Lambda context object

    Returns:
        dict: Response with statusCode and body
    """
    try:
        s3_bucket = os.getenv('ZILLOW_S3_BUCKET')

        if not s3_bucket:
            raise ValueError('ZILLOW_S3_BUCKET environment variable is required')

        # Run the scraper for all cities
        Zillow.run_all(s3_bucket=s3_bucket, s3_prefix="session_data")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully scraped Zillow data for all cities',
                'cities': Zillow.CITIES
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
