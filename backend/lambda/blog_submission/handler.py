import json
import boto3
import os

# Create an SQS client
sqs = boto3.client('sqs')
queue_url = os.environ['QUEUE_URL']

def lambda_handler(event, context):
    
    try:
        # Extract the body and parse it as JSON
        body = json.loads(event.get('body', '{}'))
        
        # Extract the fields from the body
        blog_title = body.get('title')
        blog_text = body.get('text')
        user_id = body.get('userId')

        if not blog_title or not blog_text or not user_id:
            raise ValueError("Missing required fields: title, text, or userId")

        # Prepare the message to be sent to the queue
        message = {
            'blog_title': blog_title,
            'blog_text': blog_text,
            'user_id': user_id
        }

        # Send message to SQS queue
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Blog submission received!', 'messageId': response['MessageId']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
