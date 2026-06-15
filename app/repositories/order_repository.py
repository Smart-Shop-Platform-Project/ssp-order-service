from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.order import Order, OrderItem
import logging

logger = logging.getLogger("ssp-order-service")

class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, order_data: dict, items_data: list):
        try:
            new_order = Order(**order_data)
            self.db.add(new_order)
            await self.db.flush() # Flush to get the order ID

            for item_data in items_data:
                new_item = OrderItem(order_id=new_order.id, **item_data)
                self.db.add(new_item)

            await self.db.commit()
            await self.db.refresh(new_order)
            return new_order
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating order in DB: {e}")
            raise

    async def get_order(self, order_id: str):
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        return result.scalars().first()

    async def update_order_status(self, order_id: str, status: str):
        order = await self.get_order(order_id)
        if order:
            order.status = status
            await self.db.commit()
            await self.db.refresh(order)
            return order
        return None
