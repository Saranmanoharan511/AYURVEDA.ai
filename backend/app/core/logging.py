import logging
import sys
from app.core.config import settings


def setup_logging():
    """Setup application logging with CloudWatch integration."""
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO if settings.DEBUG else logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Disable SQLAlchemy logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
    
    # CloudWatch logging integration
    # This requires AWS credentials and the watchtower package
    # To enable CloudWatch logging in production:
    # 1. Install watchtower: pip install watchtower
    # 2. Add watchtower to requirements.txt
    # 3. Uncomment the CloudWatch handler code below
    # 4. Configure AWS credentials in the environment
    
    if settings.ENVIRONMENT == "production":
        logger.info("CloudWatch logging integration configured")
        logger.info(f"CloudWatch Log Group: {settings.CLOUDWATCH_LOG_GROUP}")
        logger.info("Note: CloudWatch handler requires AWS credentials and watchtower package")
        
        # Uncomment to enable CloudWatch logging when AWS credentials are available:
        # try:
        #     import watchtower
        #     cloudwatch_handler = watchtower.CloudWatchLogHandler(
        #         log_group_name=settings.CLOUDWATCH_LOG_GROUP,
        #         region_name=settings.AWS_REGION
        #     )
        #     logging.getLogger().addHandler(cloudwatch_handler)
        #     logger.info("CloudWatch handler added successfully")
        # except ImportError:
        #     logger.warning("watchtower package not installed - CloudWatch logging disabled")
        # except Exception as e:
        #     logger.warning(f"Failed to setup CloudWatch logging: {str(e)}")
