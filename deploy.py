import boto3
import os
import time

# env
INSTANCE_ID = os.getenv('INSTANCE_ID')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')

ssm_client = boto3.client(
    'ssm', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
response = ssm_client.send_command(
    InstanceIds=[INSTANCE_ID],
    DocumentName="AWS-RunShellScript",
    Parameters={'commands': ["runuser -l ubuntu -c 'cd /opt/git/ergopad && docker compose -f docker-compose-prod.yml down && git pull && docker compose -f docker-compose-prod.yml up -d'"]})

command_id = response['Command']['CommandId']

# sync
time.sleep(2)

output = ssm_client.get_command_invocation(
    CommandId=command_id,
    InstanceId=INSTANCE_ID,
)

print(output)
