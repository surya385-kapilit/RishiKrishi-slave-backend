
import mimetypes
import boto3
import uuid
import os
from fastapi import UploadFile
from typing import Optional
from dotenv import load_dotenv
import logging
from botocore.config import Config  # Correct import

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class S3Service:
    def __init__(self):
        self.bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
        self.access_key = os.getenv("AWS_ACCESS_KEY")
        self.secret_key = os.getenv("AWS_SECRET_KEY")
        self.region = os.getenv("AWS_REGION")
        self.endpoint = os.getenv("AWS_S3_ENDPOINT")

        # Validate environment variables
        if not all(
            [
                self.bucket_name,
                self.access_key,
                self.secret_key,
                self.region,
                self.endpoint,
            ]
        ):
            raise ValueError("Missing required AWS environment variables")

        # Configure with better timeout and retry settings
        s3_config = Config(
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=90,
            read_timeout=200,
            max_pool_connections=10,
        )

        # Initialize S3 client with explicit credentials
        session = boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )

        self.s3_client = session.client(
            "s3",
            endpoint_url=self.endpoint,
            config=s3_config,
            verify=False,  # Try this if SSL certificate issues
        )
    def generate_upload_presigned_url(self, object_name: str, expiry_hours: int) -> str:
        content_type, _ = mimetypes.guess_type(object_name)
        if not content_type:
            content_type = "application/octet-stream"

        return self.s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": object_name,
                "ContentType": content_type
            },
            ExpiresIn=expiry_hours * 3600
        )

    def generate_download_presigned_url(self, object_name: str, expiry_hours: int) -> str:
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": object_name},
            ExpiresIn=expiry_hours * 3600
        )
    def _get_file_extension(self, filename: str) -> str:
        if not filename:
            return ""
        return os.path.splitext(filename)[1] or ""
    


