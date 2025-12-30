import os
import json

from zillow import Zillow


def lambda_handler(event, context):
    """
    AWS Lambda handler for Zillow scraper

    Triggered by EventBridge schedule with city-specific payload

    Environment Variables:
        ZILLOW_S3_BUCKET: S3 bucket containing session data (required)
        ZILLOW_S3_PREFIX: S3 prefix/folder for session data (default: session_data)
        PRICE_HISTORY_QUEUE_URL: SQS queue URL for price history messages (optional)

    Event Payload:
        {
            "city": "Collingswood"  # One of: Collingswood, Haddonfield, Moorestown, Haddon_Township
        }

    Args:
        event: Lambda event object with city parameter
        context: Lambda context object

    Returns:
        dict: Response with statusCode and body
    """
    try:
        s3_bucket = os.getenv('ZILLOW_S3_BUCKET')

        if not s3_bucket:
            raise ValueError('ZILLOW_S3_BUCKET environment variable is required')

        # Get city from event payload
        city = event.get('city')

        if not city:
            raise ValueError('Event must contain "city" parameter')

        # Validate city is in the allowed list
        if city not in Zillow.CITIES:
            raise ValueError(f'Invalid city: {city}. Must be one of: {", ".join(Zillow.CITIES)}')

        print(f'Starting Zillow scraper for city: {city}')

        # Create crawler instance for the specific city
        crawler, search_data = Zillow.for_city(city, s3_bucket=s3_bucket, s3_prefix="session_data")

        # Run the scraper for this city
        crawler.run(search_data)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully scraped Zillow data for {city}',
                'city': city
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
