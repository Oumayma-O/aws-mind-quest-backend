import os
import logging
from typing import Tuple, Optional
from app.config import settings

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    boto3 = None


def ensure_uploads_dir(path: str = "uploads"):
    os.makedirs(path, exist_ok=True)
    return path


def upload_file(file_obj, filename: str) -> Tuple[Optional[str], Optional[str]]:
    """Upload file either to S3 (if configured) or to local `uploads/` directory.

    Returns (s3_key, url) where one or both may be None depending on configuration.
    """
    # Prefer S3 if bucket configured and boto3 available
    bucket = getattr(settings, "AWS_S3_BUCKET", None)
    if bucket and boto3:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            region_name=getattr(settings, "AWS_REGION", None),
        )
        key = f"certifications/{filename}"
        try:
            # If object already exists in S3, return its URL and avoid re-upload
            try:
                s3.head_object(Bucket=bucket, Key=key)
                region = getattr(settings, "AWS_REGION", None) or "us-east-1"
                url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
                logger.info(f"S3 object already exists: s3://{bucket}/{key}")
                return key, url
            except ClientError:
                # Not found, proceed to upload
                pass
            # file_obj is a SpooledTemporaryFile or file-like with read()
            file_obj.seek(0)
            s3.upload_fileobj(file_obj, bucket, key)
            region = getattr(settings, "AWS_REGION", None)
            if region:
                url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
            else:
                url = f"https://{bucket}.s3.amazonaws.com/{key}"
            logger.info(f"Uploaded file to S3: s3://{bucket}/{key}")
            return key, url
        except (BotoCoreError, ClientError) as e:
            logger.exception(f"S3 upload failed for s3://{bucket}/{key}: {e}")
            return None, None
    # Fallback to local storage
    uploads_dir = ensure_uploads_dir()
    path = os.path.join(uploads_dir, filename)
    try:
        file_obj.seek(0)
        with open(path, "wb") as f:
            f.write(file_obj.read())
        url = path
        logger.info(f"Saved file locally: {path}")
        return None, url
    except Exception as e:
        logger.exception(f"Local file save failed: {e}")
        return None, None


def parse_s3_path(s3_path: str) -> tuple[str, str, str]:
    """Parse an S3 URI or HTTPS URL and return (bucket, key, url).

    Accepts forms like:
    - s3://bucket-name/path/to/object
    - https://bucket.s3.region.amazonaws.com/path/to/object
    - https://s3.region.amazonaws.com/bucket-name/path/to/object
    Returns (bucket, key, public_url)
    """
    if s3_path.startswith("s3://"):
        rest = s3_path[5:]
        parts = rest.split('/', 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ''
        region = getattr(settings, "AWS_REGION", None) or "us-east-1"
        url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
        return bucket, key, url

    # Try to parse HTTPS S3 URL
    # Example: https://bucket.s3.us-east-1.amazonaws.com/key
    if s3_path.startswith("https://") or s3_path.startswith("http://"):
        # naive parsing
        try:
            no_proto = s3_path.split('://', 1)[1]
            host, path = no_proto.split('/', 1)
            if host.endswith("amazonaws.com") and ".s3" in host:
                bucket = host.split('.s3', 1)[0]
                key = path
                return bucket, key, s3_path
            # fallback: https://s3.region.amazonaws.com/bucket/key
            if host.startswith('s3.'):
                parts = path.split('/', 1)
                bucket = parts[0]
                key = parts[1] if len(parts) > 1 else ''
                return bucket, key, s3_path
        except Exception:
            pass

    raise ValueError(f"Unable to parse S3 path: {s3_path}")


def s3_object_exists(bucket: str, key: str) -> bool:
    if not boto3:
        return False
    s3 = boto3.client(
        "s3",
        aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
        aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
        region_name=getattr(settings, "AWS_REGION", None),
    )
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        return False
