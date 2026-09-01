import pytest
from app.services.s3_service import S3Service


def test_s3_service_initialization():
    """Test that S3 service can be initialized."""
    service = S3Service()
    assert service is not None
    assert service.s3_client is not None


def test_s3_service_missing_bucket():
    """Test that S3 service handles missing bucket configuration."""
    service = S3Service()
    # When bucket name is not configured, operations should fail gracefully
    with pytest.raises(ValueError, match="S3_BUCKET_NAME not configured"):
        service.generate_presigned_upload_url("test.txt", "text/plain")
