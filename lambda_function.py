from __future__ import annotations

import boto3
import urllib.parse

from shared.validation import ValidationError, validate_raw_event_csv

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # Extract bucket and file info from the incoming S3 trigger event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    # We only care about new files landing inside raw-data/
    if not key.startswith('raw-data/') or key == 'raw-data/':
        return {'status': 'skipped', 'message': 'Not a file in raw-data/'}
        
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        csv_text = response['Body'].read().decode('utf-8')

        validated_row = validate_raw_event_csv(csv_text)
        print(f"File detected: {key} | Validated first row: {validated_row}")

        target_key = key.replace('raw-data/', 'processed-data/')

        s3_client.copy_object(Bucket=bucket, CopySource={'Bucket': bucket, 'Key': key}, Key=target_key)
        s3_client.delete_object(Bucket=bucket, Key=key)

        print(f"Validation passed. Moved {key} to {target_key}")
        return {'status': 'success', 'message': 'File validated and moved'}

    except ValidationError as e:
        print(f"Validation failed for {key}: {e.errors}")
        return {'status': 'failed', 'message': 'Invalid raw event schema', 'errors': e.errors}

    except Exception as e:
        print(f"Error processing data tracking: {e}")
        raise e
