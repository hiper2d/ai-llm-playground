import json

from dotenv import load_dotenv, find_dotenv

from api.assistant import Assistant


def lambda_handler(event, context):
    question = event['queryStringParameters']['question']
    thread_id = event['queryStringParameters']['thread_id'] if 'thread_id' in event['queryStringParameters'] else None

    assistant = Assistant(assistant_id='asst_Sian9txZgx5Br6ZFiQjBBd1b', thread_id=thread_id)
    answer = assistant.run(question)
    return answer


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    params = {
        'queryStringParameters': {
            'question': 'What is WAVE ROLL?',
            'thread_id': 'thread_nOEbqhH4TSX8gIbeMZ28jbnv'
        }
    }
    lambda_handler(params, None)
