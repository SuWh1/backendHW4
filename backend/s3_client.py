import aioboto3
from botocore.exceptions import ClientError
from typing import Optional
import uuid
from config import settings


class S3Client:
    def __init__(self):
        self.bucket_name = settings.aws_bucket_name
        self.region = settings.aws_region
        
    async def upload_file(self, file_content: bytes, filename: str, content_type: Optional[str] = None) -> Optional[dict]:
        """Upload file to S3 bucket"""
        try:
            # Generate unique key for S3
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            s3_key = f"uploads/{uuid.uuid4()}.{file_extension}" if file_extension else f"uploads/{uuid.uuid4()}"
            
            session = aioboto3.Session()
            async with session.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=self.region
            ) as s3_client:
                
                # Upload file
                await s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=content_type or 'application/octet-stream'
                )
                
                # Generate S3 URL
                s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
                
                return {
                    's3_key': s3_key,
                    's3_url': s3_url,
                    'filename': filename,
                    'content_type': content_type,
                    'file_size': len(file_content)
                }
                
        except ClientError as e:
            print(f"S3 upload error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error during S3 upload: {e}")
            return None
    
    async def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3 bucket"""
        try:
            session = aioboto3.Session()
            async with session.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=self.region
            ) as s3_client:
                
                await s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
                return True
                
        except ClientError as e:
            print(f"S3 delete error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during S3 delete: {e}")
            return False


# Global S3 client instance
s3_client = S3Client() 