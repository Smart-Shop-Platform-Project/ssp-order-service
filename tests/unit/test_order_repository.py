import pytest
from app.repositories.order_repository import OrderRepository
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order

# We use the db_session fixture provided by conftest.py, which uses an in-memory SQLite DB
@pytest.fixture
def repo(db_session: AsyncSession):
    return OrderRepository(db_session)

@pytest.mark.asyncio
async def test_create_order_repository(repo: OrderRepository):
    # Setup data
    order_data = {"user_id": "test_user_1", "total_amount": 100.0}
    items_data = [
        {"product_id": "prod_a", "quantity": 1, "price_at_purchase": 50.0},
        {"product_id": "prod_b", "quantity": 2, "price_at_purchase": 25.0}
    ]

    # Execute
    new_order = await repo.create_order(order_data, items_data)

    # Assert
    assert new_order is not None
    assert new_order.id is not None
    assert new_order.user_id == "test_user_1"
    assert new_order.total_amount == 100.0
    assert new_order.status == "PENDING"
    assert len(new_order.items) == 2
    
    item_product_ids = [item.product_id for item in new_order.items]
    assert "prod_a" in item_product_ids
    assert "prod_b" in item_product_ids

@pytest.mark.asyncio
async def test_get_order(repo: OrderRepository):
    # Setup: Create an order first
    order_data = {"user_id": "test_user_2", "total_amount": 75.0}
    created_order = await repo.create_order(order_data, [])

    # Execute
    fetched_order = await repo.get_order(created_order.id)

    # Assert
    assert fetched_order is not None
    assert fetched_order.id == created_order.id
    assert fetched_order.user_id == "test_user_2"

@pytest.mark.asyncio
async def test_update_order_status(repo: OrderRepository):
    # Setup: Create an order
    order_data = {"user_id": "test_user_3", "total_amount": 50.0}
    created_order = await repo.create_order(order_data, [])

    # Execute
    updated_order = await repo.update_order_status(created_order.id, "CONFIRMED")

    # Assert
    assert updated_order is not None
    assert updated_order.status == "CONFIRMED"
    
    # Verify in DB
    fetched_order = await repo.get_order(created_order.id)
    assert fetched_order.status == "CONFIRMED"

@pytest.mark.asyncio
async def test_update_order_status_not_found(repo: OrderRepository):
    # Execute with non-existent ID
    updated_order = await repo.update_order_status("nonexistent_id", "CONFIRMED")

    # Assert
    assert updated_order is None
