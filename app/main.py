from fastapi import FastAPI
import logging
import sys
from .core.database import engine
from .api.order_routes import router as order_router
from .events.kafka_producer import get_kafka_producer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "message":"%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ssp-order-service")

app = FastAPI(title="SSP Order Service")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Order Service...")
    # The database connection and Kafka producer are initialized lazily 
    # via dependency injection or singletons when needed.

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Order Service...")
    producer = get_kafka_producer()
    if producer:
        producer.close()
    await engine.dispose()

app.include_router(order_router, prefix="/api/v1")

@app.get("/", tags=["Health Check"])
async def root():
    return {"message": "SSP Order Service is running"}
