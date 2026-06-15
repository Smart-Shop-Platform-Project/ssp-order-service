from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..services.order_service import OrderService
from ..events.kafka_producer import get_kafka_producer, KafkaProducerService
from pydantic import BaseModel
from typing import List

router = APIRouter()

class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int
    price_at_purchase: float

class OrderCreate(BaseModel):
    user_id: str
    total_amount: float
    items: List[OrderItemCreate]

@router.post("/orders", status_code=201, tags=["Orders"])
async def create_new_order(
    order: OrderCreate, 
    db: AsyncSession = Depends(get_db),
    producer: KafkaProducerService = Depends(get_kafka_producer)
):
    service = OrderService(db, producer)
    new_order = await service.create_order(order.dict())
    return {"message": "Order created successfully", "order_id": new_order.id}
