import json
import os
import subprocess
import sys

# Install packages in the /tmp directory
def install_package(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-t', '/tmp'])

install_package('requests')
install_package('requests-aws4auth')

# Add /tmp to the system path
sys.path.append('/tmp')

import requests
from requests_aws4auth import AWS4Auth
import boto3

# Set your OpenSearch endpoint here
OPENSEARCH_ENDPOINT = os.environ['OPENSEARCH_ENDPOINT']

# Get AWS credentials for signing the request
session = boto3.Session()
credentials = session.get_credentials().get_frozen_credentials()

region = 'ap-south-1'

# AWS Signature Version 4 Auth
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

def lambda_handler(event, context):
    
    # Extract the search term from the query string parameters
    search_term = event.get('queryStringParameters', {}).get('query', '')

    if not search_term:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Query parameter "query" is missing'
            })
        }

    # Construct the search query
    search_query = {
        "query": {
            "bool": {
                "should": [
                    {
                        "match": {
                            "blog_title": search_term
                        }
                    },
                    {
                        "match": {
                            "blog_text": search_term
                        }
                    }
                ]
            }
        }
    }

    # Make the request to OpenSearch with AWS SigV4 signing
    headers = {"Content-Type": "application/json"}
    response = requests.get(f'https://{OPENSEARCH_ENDPOINT}/blogs/_search', 
                            auth=awsauth, 
                            headers=headers, 
                            json=search_query)

    # Check for errors
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': json.dumps({'error': response.text})
        }

    # Parse the response JSON and extract documents
    response_json = response.json()
    hits = response_json.get('hits', {}).get('hits', [])

    # Extract only the _source field (documents)
    documents = [hit.get('_source') for hit in hits]

    # Return the extracted documents
    return {
        'statusCode': 200,
        'body': json.dumps(documents)
    }
