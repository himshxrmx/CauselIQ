import boto3
import json

REGION = "us-east-1"
FUNCTION_NAME = "CauseIQ-Backend"

lambda_client = boto3.client('lambda', region_name=REGION)
apigw = boto3.client('apigatewayv2', region_name=REGION)

print("Getting Lambda ARN...")
fn = lambda_client.get_function(FunctionName=FUNCTION_NAME)
lambda_arn = fn['Configuration']['FunctionArn']

print("Creating HTTP API Gateway...")
api = apigw.create_api(
    Name='CauseIQ-API',
    ProtocolType='HTTP',
    CorsConfiguration={
        'AllowOrigins': ['*'],
        'AllowMethods': ['*'],
        'AllowHeaders': ['*']
    }
)
api_id = api['ApiId']
api_endpoint = api['ApiEndpoint']

print(f"API created with ID: {api_id}")

print("Creating Integration...")
integration = apigw.create_integration(
    ApiId=api_id,
    IntegrationType='AWS_PROXY',
    IntegrationUri=lambda_arn,
    PayloadFormatVersion='2.0'
)
integration_id = integration['IntegrationId']

print("Creating Route...")
apigw.create_route(
    ApiId=api_id,
    RouteKey='ANY /{proxy+}',
    Target=f"integrations/{integration_id}"
)

print("Creating Stage...")
apigw.create_stage(
    ApiId=api_id,
    StageName='$default',
    AutoDeploy=True
)

print("Adding permission for API Gateway to invoke Lambda...")
try:
    lambda_client.add_permission(
        FunctionName=FUNCTION_NAME,
        StatementId='APIGatewayInvoke',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f"arn:aws:execute-api:{REGION}:{fn['Configuration']['FunctionArn'].split(':')[4]}:{api_id}/*/*"
    )
except lambda_client.exceptions.ResourceConflictException:
    print("Permission already exists")

print("\n========================================")
print(f"✅ API Gateway Deployment Complete!")
print(f"🚀 LIVE API URL: {api_endpoint}")
print("========================================\n")
