from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.order_repository import OrderRepository
from ..events.kafka_producer import KafkaProducerService
from fastapi import HTTPException
import logging

logger = logging.getLogger("ssp-order-service")

class OrderService:
    def __init__(self, db: AsyncSession, producer: KafkaProducerService):
        self.repository = OrderRepository(db)
        self.producer = producer

    async def create_order(self, order_data: dict):
        # Here you would typically have more business logic:
        # 1. Call the cart service to get cart contents
        # 2. Call the product service to verify prices and stock
        # 3. Call the payment service to create a payment intent
        # For now, we'll assume the input is validated
        
        items_data = order_data.pop("items", [])
        
        try:
            new_order = await self.repository.create_order(order_data, items_data)
            
            # After successfully saving to DB, publish the event
            await self.producer.send_event('order_created', {
                "order_id": new_order.id,
                "user_id": new_order.user_id,
                "total_amount": new_order.total_amount,
                "items": [{"product_id": item.product_id, "quantity": item.quantity} for item in new_order.items]
            })
            
            return new_order
        except Exception as e:
            logger.error(f"Service layer error creating order: {e}")
            raise HTTPException(status_code=500, detail="Could not create order.")
