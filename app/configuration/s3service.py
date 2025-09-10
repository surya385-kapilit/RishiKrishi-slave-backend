
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

    async def upload_file(self, file: UploadFile) -> Optional[str]:
        try:
            # Get file extension and content type
            file_extension = self._get_file_extension(file.filename).lower()
            content_type = file.content_type

            # Validate file type and size based on category
            if file_extension in [".jpg", ".jpeg", ".png", ".jfif"]:
                max_size = 20 * 1024 * 1024
            elif file_extension in [".mp4", ".mov", ".avi", ".mkv"]:
                max_size = 1024 * 1024 * 1024
            elif file_extension in [
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
            ]:
                max_size = 500 * 1024 * 1024
            else:
                max_size = 500 * 1024 * 1024

            if file.size > max_size:
                raise ValueError(f"File size exceeds {max_size/(1024*1024)}MB limit")

            # Generate unique filename
            if file_extension in [".jpg", ".jpeg", ".png", ".jfif"]:
                folder = "images"
            elif file_extension in [".mp4", ".mov", ".avi", ".mkv"]:
                folder = "videos"
            elif file_extension in [
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
            ]:
                folder = "documents"
            else:
                folder = "others"

            file_name = f"rishikrish/{folder}/{uuid.uuid4()}{file_extension}"

            # Read file content
            content = await file.read()

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=content,
                ContentType=content_type,
            )

            return f"{self.endpoint}{self.bucket_name}/{file_name}"

        except Exception as e:
            logger.error(f"S3 upload failed for {file.filename}: {str(e)}")
            raise Exception(f"S3 upload failed: {str(e)}")

    def _get_file_extension(self, filename: str) -> str:
        if not filename:
            return ""
        return os.path.splitext(filename)[1] or ""
