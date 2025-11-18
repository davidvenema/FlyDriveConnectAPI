import os
import boto3
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from security import get_current_member
from datetime import timedelta

router = APIRouter(prefix="/upload", tags=["uploads"])

S3_BUCKET = os.getenv("S3_BUCKET")
if not S3_BUCKET:
    raise RuntimeError("S3_BUCKET not set in environment")

s3_client = boto3.client("s3")


# -------------------------
# Request schema
# -------------------------
class PresignRequest(BaseModel):
    car_id: int
    booking_id: int | None = None   # gallery images won’t have booking_id
    phase: str | None = None        # before / after
    angle: str | None = None        # left, right, front, etc.
    is_gallery: bool = False        # true for marketing photos


# -------------------------
# Generate S3 key
# -------------------------
def build_s3_key(req: PresignRequest) -> str:

    if req.is_gallery:
        # /cars/{car_id}/gallery/1.jpg
        return f"cars/{req.car_id}/gallery/1.jpg"

    # booking photos:
    # cars/{car_id}/bookings/{booking_id}/{phase}/{angle}.jpg
    if not req.booking_id or not req.phase or not req.angle:
        raise ValueError("booking_id, phase, and angle are required for inspection photos")

    return (
        f"cars/{req.car_id}/bookings/"
        f"{req.booking_id}/{req.phase}/{req.angle}.jpg"
    )


# -------------------------
# Main endpoint
# -------------------------
@router.post("/presign")
def get_presigned_upload_url(
    req: PresignRequest,
    user=Depends(get_current_member),  # authenticated caller
):
    try:
        key = build_s3_key(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        upload_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": key,
                "ContentType": "image/jpeg",
            },
            ExpiresIn=60 * 10  # 10 minutes
        )
    except Exception as e:
        raise HTTPException(500, f"Could not create presigned URL: {e}")

    # Public URL for reading the image later
    public_url = f"https://{S3_BUCKET}.s3.ap-southeast-2.amazonaws.com/{key}"

    return {
        "upload_url": upload_url,
        "public_url": public_url,
        "key": key
    }
