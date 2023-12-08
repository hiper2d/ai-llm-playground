import json


def lambda_handler(event, context):
    personId = event['queryStringParameters']['personId']

    return {
        'statusCode': 200,
        'body': json.dumps({
            'personId': personId
        })
    }