from pydantic_settings import BaseSettings
import os
import boto3
import logging

logger = logging.getLogger("ssp-order-service")

def get_ssm_parameter(name, region):
    try:
        ssm_client = boto3.client('ssm', region_name=region)
        parameter = ssm_client.get_parameter(Name=name, WithDecryption=True)
        return parameter['Parameter']['Value']
    except Exception as e:
        logger.critical(f"Error fetching parameter {name}: {e}")
        raise

class Settings(BaseSettings):
    AWS_REGION: str = os.environ.get("AWS_REGION", "us-east-1")
    KAFKA_BROKER_URL_PARAM_NAME: str = os.environ.get("KAFKA_BROKER_URL_PARAM_NAME", "/ssp/shared/kafka_broker_url")
    # For local development, fallback to a local postgres instance. In ECS, this parameter name is passed via env var.
    DATABASE_URL_PARAM_NAME: str = os.environ.get("DATABASE_URL_PARAM_NAME", "/ssp/order/database_url")
    DATABASE_URL: str = ""
    KAFKA_BROKER_URL: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # We need asyncpg for asynchronous operations with SQLAlchemy
        try:
            db_url = get_ssm_parameter(self.DATABASE_URL_PARAM_NAME, self.AWS_REGION)
            # SQLAlchemy asyncpg requires postgresql+asyncpg:// instead of postgres:// or postgresql://
            self.DATABASE_URL = db_url.replace("postgresql://", "postgresql+asyncpg://").replace("postgres://", "postgresql+asyncpg://")
        except Exception:
             self.DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/ssp_orders"
        
        try:
            self.KAFKA_BROKER_URL = get_ssm_parameter(self.KAFKA_BROKER_URL_PARAM_NAME, self.AWS_REGION)
        except Exception:
            self.KAFKA_BROKER_URL = "localhost:9092"

settings = Settings()
