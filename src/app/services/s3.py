from typing import BinaryIO
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.core.logging import app_logger


class S3Service:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )
        self.bucket = settings.s3_bucket_name

    def upload_image(self, file: BinaryIO, content_type: str, ext: str = "jpg") -> str:
        key = f"articles/{uuid.uuid4()}.{ext}"

        logger = app_logger.bind(bucket=self.bucket, key=key, content_type=content_type)
        logger.info("S3 image upload started")

        try:
            self.client.upload_fileobj(
                file, self.bucket, key, ExtraArgs={"ContentType": content_type}
            )
        except (BotoCoreError, ClientError) as e:
            logger.exception("S3 image upload failed")
            raise RuntimeError(f"S3 upload failed: {e}") from e

        image_url = f"{settings.s3_endpoint_url}/{self.bucket}/{key}"
        logger.info("S3 image upload successfully", image_url=image_url)
        return image_url

    def delete_image(self, url: str) -> None:
        key = url.split(f"{self.bucket}/", 1)[-1]

        logger = app_logger.bind(bucket=self.bucket, key=key)
        logger.info("S3 image delete started")

        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except (BotoCoreError, ClientError) as e:
            logger.exception("S3 image delete failed")
            raise RuntimeError(f"S3 delete failed: {e}") from e

        logger.info("S3 image delete successfully")


s3_service = S3Service()
