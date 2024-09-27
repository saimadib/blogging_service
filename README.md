# Blogging Service

## Overview

The Blogging Service is a serverless application built with AWS CDK that allows users to submit and search for blog posts using AWS Lambda, Amazon SQS, and Amazon OpenSearch.

![Blogging Service Architecture](https://github.com/user-attachments/assets/46cd3016-09f9-4444-9906-8c9f6c9af533)

## Architecture

- **API Gateway**: Entry point for HTTP requests.
  - **POST `/blogs`**: Triggers the **Blog Submission Lambda Function**.
  - **GET `/blogs/search`**: Triggers the **Search Lambda Function**.

- **Lambda Functions**:
  - **Blog Submission Function**: Sends new blogs to SQS.
  - **Blog Processing Function**: Processes SQS messages and writes to OpenSearch.
  - **Search Function**: Queries OpenSearch for blog data.

- **SQS Queue**: Buffers submissions for asynchronous processing.

- **OpenSearch**: Stores blog data for efficient retrieval.

## Requirements

1. **Node.js** (14.x or later)
2. **AWS CDK** (2.x)
3. **AWS Account** with appropriate permissions.
4. **AWS CLI** configured with credentials.

## Setup Instructions

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/saimadib/blogging_service.git
   cd blogging_service
   
2. **Install AWS CDK Globally (if not already installed)**:

   ```bash
   npm install -g aws-cdk

3. **Install Project Dependencies**:

   ```bash
   npm install

4. **Bootstrap Your AWS Environment (if not already done)**:

   ```bash
   cdk bootstrap

5. **Deploy the Stack**:

   ```bash
   cdk deploy

## API Usage

After deployment, you can interact with the API using the following endpoints. These resources are already deployed for testing purposes.

### Submit a Blog

To submit a new blog post, use the following command:

    curl -X POST https://lysxoh2iwl.execute-api.ap-south-1.amazonaws.com/prod/blogs \
    -H "Content-Type: application/json" \
    -d '{"title": "My Blog Post", "text": "This is the content of my blog post.", "userId": "789456"}'

### Search Blogs

To search for blogs, use the following command:

    curl -X GET "https://lysxoh2iwl.execute-api.ap-south-1.amazonaws.com/prod/blogs/search?query=<YOUR_QUERY>"
