from logger import logger
import json


def lambda_handler(event, context):
    logger.info(f"Exception handler: EVENT: {json.dumps(event)}, CONTEXT: {json.dumps(context)}")
    return {
        'statusCode': 200,
        'body': ""
    }
    