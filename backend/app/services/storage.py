"""Complaint image storage backends."""
from pathlib import Path

from app.core.config import settings


def storage_is_s3() -> bool:
    return settings.complaint_image_storage.strip().lower() in {"s3", "object", "object_storage"}


def _s3_client():
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("S3 object storage requires the boto3 dependency") from exc

    kwargs = {"region_name": settings.s3_region or None}
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    if settings.s3_access_key_id and settings.s3_secret_access_key:
        kwargs["aws_access_key_id"] = settings.s3_access_key_id
        kwargs["aws_secret_access_key"] = settings.s3_secret_access_key
    return boto3.client("s3", **kwargs)


def save_s3(key: str, content: bytes, content_type: str) -> None:
    if not settings.s3_bucket:
        raise RuntimeError("S3_BUCKET is required for object image storage")
    _s3_client().put_object(
        Bucket=settings.s3_bucket,
        Key=f"complaint-images/{key}",
        Body=content,
        ContentType=content_type,
        ServerSideEncryption="AES256",
    )


def presigned_s3_url(key: str) -> str:
    if not settings.s3_bucket:
        raise RuntimeError("S3_BUCKET is required for object image storage")
    if settings.s3_public_url:
        return f"{settings.s3_public_url.rstrip('/')}/complaint-images/{key}"
    return _s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": f"complaint-images/{key}"},
        ExpiresIn=300,
    )


def local_image_path(storage_key: str) -> Path:
    storage_dir = Path(settings.complaint_upload_dir).resolve()
    key_path = Path(storage_key)
    if key_path.name != storage_key:
        raise ValueError("Invalid stored image reference")
    image_path = (storage_dir / key_path.name).resolve()
    if image_path.parent != storage_dir:
        raise ValueError("Invalid upload storage path")
    return image_path
