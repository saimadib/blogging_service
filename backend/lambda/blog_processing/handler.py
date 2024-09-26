import boto3
import json
import subprocess
import sys
import os

# Install packages in the /tmp directory
def install_package(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-t', '/tmp'])

install_package('requests-aws4auth')
install_package('requests')

# Add /tmp to the system path
sys.path.append('/tmp')

# Import the packages after installation
from requests_aws4auth import AWS4Auth
import requests

# Initialize AWS credentials and OpenSearch endpoint
region = 'ap-south-1' 
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key, 
    credentials.secret_key, 
    region, 
    service, 
    session_token=credentials.token
)

# Get the OpenSearch domain endpoint from environment variable
host = os.environ.get('OPENSEARCH_ENDPOINT')  
index = 'blogs'  
url = f"https://{host}/{index}/_doc/"  # The endpoint for indexing documents

def lambda_handler(event, context):
    
    # Initialize a response structure
    response = {
        "statusCode": 200,
        "body": ''
    }

    # Loop through each record in the SQS event
    for record in event['Records']:
        # Get the message from SQS
        message = json.loads(record['body'])

        # Prepare the document to be indexed in OpenSearch
        document = {
            'blog_title': message.get('blog_title'),
            'blog_text': message.get('blog_text'),
            'user_id': message.get('user_id')
        }

        try:
            # Make the signed HTTP request to index the document
            headers = {"Content-Type": "application/json"}
            r = requests.post(url, auth=awsauth, headers=headers, data=json.dumps(document))
            r.raise_for_status() 

        except requests.exceptions.RequestException as e:
            # Handle any request exceptions
            response['statusCode'] = 500
            response['body'] = json.dumps({"error": str(e)})
            print(f"Error indexing document: {str(e)}")  # Debugging: print the error
            return response
    
    response['body'] = json.dumps({'message': 'Documents indexed successfully'})
    return response
