import boto3
from botocore.config import Config
import os
import json
from app.core.logging import logger

FLOCI_ENDPOINT = os.getenv("FLOCI_ENDPOINT_URL", "http://floci:4566")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
QUEUE_NAME = "datapulse-ai-queries"
QUEUE_URL = f"{FLOCI_ENDPOINT}/000000000000/{QUEUE_NAME}"

_sqs_client = None

def get_sqs_client():
    global _sqs_client
    if _sqs_client is None:
        _sqs_client = boto3.client(
            "sqs",
            endpoint_url=FLOCI_ENDPOINT,
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
            config=Config(signature_version="v4"),
        )
    return _sqs_client

async def publish_query(job_id: str, question: str, language: str = "en", username: str = "admin") -> bool:
    try:
        client = get_sqs_client()
        client.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps({
                "job_id": job_id,
                "question": question,
                "language": language,
                "username": username,
            }),
        )
        logger.info("sqs_message_published", job_id=job_id)
        return True
    except Exception as e:
        logger.error("sqs_publish_failed", job_id=job_id, error=str(e))
        return False
    
async def receive_messages(max_messages: int = 1) -> list[dict]:
    try:
        client = get_sqs_client()
        response = client.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=0,
        )
        messages = []
        for msg in response.get("Messages", []):
            body =  json.loads(msg["Body"])
            body["receipt_handle"] = msg["ReceiptHandle"]
            messages.append(body)
        if messages:
            logger.info("sqs_messages_received", count=len(messages))
        return messages
    except Exception as e:
        logger.error("sqs_receive_failed", error=str(e))
        return []
    
async def delete_message(receipt_handle: str) -> bool:
    try:
        client = get_sqs_client()
        client.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=receipt_handle,
        )
        logger.info("sqs_message_deleted")
        return True
    except Exception as e:
        logger.error("sqs_delete_failed", error=str(e))
        return False