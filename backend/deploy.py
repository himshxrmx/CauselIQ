import os
import shutil
import subprocess
import zipfile
import boto3
import json
import time

FUNCTION_NAME = "CauseIQ-Backend"
ROLE_NAME = "CauseIQLambdaRole"
REGION = "us-east-1"

print("Parsing env...")
env_vars = {}
with open(".env") as f:
    for line in f:
        if line.strip() and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env_vars[k] = v

print("1. Packaging dependencies...")
if os.path.exists("package"):
    shutil.rmtree("package")
os.makedirs("package")
subprocess.check_call([
    "pip", "install", "-r", "requirements.txt", 
    "-t", "package/", 
    "--platform", "manylinux2014_x86_64", 
    "--only-binary=:all:", 
    "--python-version", "3.12"
])

print("Copying source files...")
shutil.copy("main.py", "package/")
shutil.copy("ai_analyzer.py", "package/")
shutil.copy("aws_client.py", "package/")

print("2. Zipping payload...")
with zipfile.ZipFile("deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk("package"):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, "package")
            zipf.write(file_path, arcname)

print("3. Deploying to AWS Lambda...")
iam = boto3.client('iam', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)

assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
}

try:
    print("Creating IAM role...")
    role_response = iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(assume_role_policy)
    )
    iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
    iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/CloudWatchLogsReadOnlyAccess")
    print("Waiting 15 seconds for IAM role propagation...")
    time.sleep(15)
    role_arn = role_response['Role']['Arn']
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']
    print("IAM role already exists.")

with open("deployment.zip", "rb") as f:
    zip_bytes = f.read()

try:
    print("Creating Lambda function...")
    lambda_response = lambda_client.create_function(
        FunctionName=FUNCTION_NAME,
        Runtime='python3.12',
        Role=role_arn,
        Handler='main.handler',
        Code={'ZipFile': zip_bytes},
        Timeout=60,
        MemorySize=512,
        Environment={'Variables': {'GOOGLE_API_KEY': env_vars.get('GOOGLE_API_KEY', '')}}
    )
except lambda_client.exceptions.ResourceConflictException:
    print("Function exists. Updating code and configuration...")
    lambda_client.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=zip_bytes)
    lambda_client.update_function_configuration(
        FunctionName=FUNCTION_NAME,
        Handler='main.handler',
        Environment={'Variables': {'GOOGLE_API_KEY': env_vars.get('GOOGLE_API_KEY', '')}},
        Timeout=60,
        MemorySize=512,
        Runtime='python3.12'
    )

print("Configuring Function URL...")
try:
    url_response = lambda_client.create_function_url_config(
        FunctionName=FUNCTION_NAME,
        AuthType='NONE'
    )
    api_url = url_response['FunctionUrl']
except lambda_client.exceptions.ResourceConflictException:
    url_response = lambda_client.get_function_url_config(FunctionName=FUNCTION_NAME)
    api_url = url_response['FunctionUrl']

try:
    lambda_client.add_permission(
        FunctionName=FUNCTION_NAME,
        StatementId='FunctionURLAllowPublicAccess',
        Action='lambda:InvokeFunctionUrl',
        Principal='*',
        FunctionUrlAuthType='NONE'
    )
except lambda_client.exceptions.ResourceConflictException:
    pass

print(f"\n✅ Deployment Complete!")
print(f"🚀 LIVE API URL: {api_url}")
