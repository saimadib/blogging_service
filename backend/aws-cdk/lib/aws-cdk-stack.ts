import * as cdk from 'aws-cdk-lib';
import { Stack, StackProps } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as opensearch from 'aws-cdk-lib/aws-opensearchservice';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import { Construct } from 'constructs';

export class AwsCdkStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // SQS Queue for blog submissions
    const blogQueue = new sqs.Queue(this, 'BlogSubmissionQueue', {
      visibilityTimeout: cdk.Duration.seconds(300),
    });

    // OpenSearch domain
    const openSearchDomain = new opensearch.CfnDomain(this, 'OpenSearchDomain', {
      domainName: 'blogs', 
      nodeToNodeEncryptionOptions: {
        enabled: true
      },
      domainEndpointOptions: {
        enforceHttps: true,
        tlsSecurityPolicy: 'Policy-Min-TLS-1-2-2019-07' 
      },
      clusterConfig: {
        instanceType: 't2.small.search', 
        instanceCount: 1, 
        dedicatedMasterEnabled: false, 
      },
      ebsOptions: {
        ebsEnabled: true, 
        volumeSize: 20, 
        volumeType: 'gp2', 
      },
    });

    // Lambda function to handle blog submission
    const blogSubmissionFunction = new lambda.Function(this, 'BlogSubmissionFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.lambda_handler',
      code: lambda.Code.fromAsset('../lambda/blog_submission'),
      environment: {
        QUEUE_URL: blogQueue.queueUrl,
      },
    });

    // Allow Lambda to send messages to SQS
    blogQueue.grantSendMessages(blogSubmissionFunction);

    // Lambda function to process SQS messages and write to OpenSearch
    const blogProcessingFunction = new lambda.Function(this, 'BlogProcessingFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.lambda_handler',
      code: lambda.Code.fromAsset('../lambda/blog_processing'), 
      environment: {
        OPENSEARCH_ENDPOINT: openSearchDomain.attrDomainEndpoint, // Endpoint for OpenSearch
        INDEX_NAME: 'blogs', // Index name in OpenSearch
      },
    });

    // Allow Lambda to read messages from SQS
    blogQueue.grantConsumeMessages(blogProcessingFunction);

    // IAM Policy to allow Lambda to write to OpenSearch
    const openSearchPolicy = new iam.PolicyStatement({
      actions: ['es:ESHttpPut', 'es:ESHttpPost'],
      resources: [openSearchDomain.attrArn + '/*'], // Allow access to the OpenSearch domain
    });
    blogProcessingFunction.addToRolePolicy(openSearchPolicy);

    // Set up SQS trigger for the blog processing function
    blogProcessingFunction.addEventSource(new lambdaEventSources.SqsEventSource(blogQueue));

    // Lambda function to handle search requests
    const searchFunction = new lambda.Function(this, 'SearchFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.lambda_handler',
      code: lambda.Code.fromAsset('../lambda/search_function'), 
      environment: {
        OPENSEARCH_ENDPOINT: openSearchDomain.attrDomainEndpoint, 
        INDEX_NAME: 'blogs', 
      },
    });

    // IAM Policy to allow Lambda to read from OpenSearch
    const searchPolicy = new iam.PolicyStatement({
      actions: ['es:ESHttpGet'],
      resources: [openSearchDomain.attrArn + '/*'], // Allow access to the OpenSearch domain
    });
    searchFunction.addToRolePolicy(searchPolicy);

    // API Gateway for the blog submission endpoint
    const api = new apigateway.RestApi(this, 'BlogApi', {
      restApiName: 'Blog Service',
    });

    const blogs = api.root.addResource('blogs');
    
    // POST method for submitting blogs
    const submitBlogIntegration = new apigateway.LambdaIntegration(blogSubmissionFunction);
    blogs.addMethod('POST', submitBlogIntegration);

    // GET method for searching blogs
    const searchIntegration = new apigateway.LambdaIntegration(searchFunction);
    const search = blogs.addResource('search');
    search.addMethod('GET', searchIntegration);
  }
}
