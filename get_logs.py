import boto3
import json

client = boto3.client('logs', region_name='us-east-1')

print("Fetching recent logs from /aws/lambda/CauseIQ-Backend...")

response = client.filter_log_events(
    logGroupName='/aws/lambda/CauseIQ-Backend',
    limit=50
)

logs = []
for event in response.get('events', []):
    message = event['message'].strip()
    if message:
        logs.append(message)

with open('my_aws_logs.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(logs))

print(f"Saved {len(logs)} log events to my_aws_logs.txt")
