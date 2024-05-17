import os
from io import BytesIO

import boto3
from botocore.exceptions import NoCredentialsError, BotoCoreError, PartialCredentialsError
from dotenv import load_dotenv
from loguru import logger
from botocore.config import Config
from boto3.session import Session

s3 = boto3.client('s3')
load_dotenv()


class S3Manager:
    def __init__(self):
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            logger.error("AWS credentials not available")
            raise ValueError("AWS credentials not available")

        # Create a session with a custom configuration
        session = Session(aws_access_key_id=self.aws_access_key_id,
                          aws_secret_access_key=self.aws_secret_access_key)

        # Create a custom configuration
        config = Config(
            max_pool_connections=50,  # Increase the maximum size of the connection pool
        )

        # Use the custom configuration when creating the S3 client
        self.s3 = session.client('s3', config=config)

    def upload_to_s3(self, file_data, s3_file_name, bucket_name):
        try:
            self.s3.upload_fileobj(file_data, bucket_name, s3_file_name)
            logger.info("Upload Successful")
            return True
        except FileNotFoundError:
            logger.error("The file was not found")
            return False
        except NoCredentialsError:
            logger.error("No AWS credentials were provided")
            return False
        except PartialCredentialsError:
            logger.error("Incomplete AWS credentials were provided")
            return False
        except BotoCoreError as e:
            logger.error(f"BotoCore Error: {e}")
            return False

    def download_from_s3(self, s3_file_name, bucket_name):
        try:
            file_data = BytesIO()
            self.s3.download_fileobj(bucket_name, s3_file_name, file_data)
            file_data.seek(0)
            logger.info("Download Successful")
            return file_data
        except FileNotFoundError:
            logger.error("The file was not found")
            return None
        except NoCredentialsError:
            logger.error("No AWS credentials were provided")
            return None
        except PartialCredentialsError:
            logger.error("Incomplete AWS credentials were provided")
            return None
        except BotoCoreError as e:
            logger.error(f"BotoCore Error: {e}")
            return None

    def set_bucket_lifecycle_configuration(self, bucket_name):
        lifecycle_configuration = {
            'Rules': [
                {
                    'ID': 'Expire files after 1 days',
                    'Status': 'Enabled',
                    'Filter': {},
                    'Expiration': {
                        'Days': 1
                    }
                }
            ]
        }

        self.s3.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_configuration
        )
        logger.info(f"Set lifecycle configuration for bucket {bucket_name}")

