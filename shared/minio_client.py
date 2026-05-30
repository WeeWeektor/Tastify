import json
import logging
import os
import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class StorageUploadError(Exception):
    """Кастомний виняток для помилок завантаження файлів у сховище."""
    pass


class MinioStorageService:
    def __init__(self):
        self.region = getattr(settings, 'MINIO_REGION')

        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name=self.region
        )
        self.public_url_base = settings.MINIO_PUBLIC_URL

    def _ensure_bucket_exists(self, bucket_name: str):
        """Перевіряє чи існує бакет, і створює його з публічним доступом, якщо ні."""
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                logger.info(f"Creating a new bucket: {bucket_name}")
                self.s3_client.create_bucket(Bucket=bucket_name)

                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "PublicRead",
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                        }
                    ]
                }

                self.s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(policy)
                )
            else:
                logger.error(f"Error accessing the bucket {bucket_name}: {e}")
                raise

    def upload_file(self, file_obj: UploadedFile, bucket_name: str, folder: str = "") -> str:
        """
        Завантажує файл у MinIO та повертає публічний URL.
        """
        self._ensure_bucket_exists(bucket_name)

        ext = os.path.splitext(file_obj.name)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        object_name = f"{folder}/{unique_filename}" if folder else unique_filename
        object_name = object_name.strip("/")

        try:
            self.s3_client.upload_fileobj(
                file_obj.file,
                bucket_name,
                object_name,
                ExtraArgs={'ContentType': file_obj.content_type}
            )

            return f"{self.public_url_base}/{bucket_name}/{object_name}"

        except ClientError as e:
            logger.error(f"File upload error in MinIO: {e}")
            raise StorageUploadError(_("Failed to upload file to storage."))


_minio_service_instance = None

def get_minio_service():
    global _minio_service_instance
    if _minio_service_instance is None:
        _minio_service_instance = MinioStorageService()
    return _minio_service_instance
