from kafka import KafkaProducer
import json
import logging
from ..core.config import settings

logger = logging.getLogger("ssp-order-service")

class KafkaProducerService:
    def __init__(self):
        self.producer = None
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BROKER_URL,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info(f"Kafka producer connected to {settings.KAFKA_BROKER_URL}")
        except Exception as e:
            logger.critical(f"Failed to initialize Kafka producer: {e}")

    async def send_event(self, topic: str, message: dict):
        if not self.producer:
            logger.error("Cannot send event, producer is not available.")
            return
            
        try:
            logger.info(f"Sending event to topic '{topic}': {message}")
            self.producer.send(topic, message)
            self.producer.flush() # Ensure message is sent
        except Exception as e:
            logger.error(f"Failed to send event to Kafka topic {topic}: {e}")
            # In a real app, you might want a more robust retry/dead-letter queue here
            raise

    def close(self):
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed.")

# Singleton instance
kafka_producer_service = KafkaProducerService()

def get_kafka_producer():
    return kafka_producer_service
