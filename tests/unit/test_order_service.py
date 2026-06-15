import pytest
from unittest.mock import AsyncMock
from app.services.order_service import OrderService
from app.models.order import Order
from fastapi import HTTPException

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.fixture
def mock_kafka_producer():
    return AsyncMock()

@pytest.fixture
def order_service(mock_db_session, mock_kafka_producer):
    # The service expects a repository, so we mock that layer
    with patch("app.services.order_service.OrderRepository") as MockRepo:
        mock_repo_instance = AsyncMock()
        MockRepo.return_value = mock_repo_instance
        
        service = OrderService(mock_db_session, mock_kafka_producer)
        service.repository = mock_repo_instance
        return service

@pytest.mark.asyncio
async def test_create_order_success(order_service, mock_kafka_producer):
    # Setup
    order_data = {"user_id": "user123", "total_amount": 150.50}
    items_data = [{"product_id": "prod1", "quantity": 2, "price_at_purchase": 75.25}]
    
    # Mock the repository to return a new order
    new_order = Order(id="order1", **order_data)
    new_order.items = [] # Simulate empty items list initially
    order_service.repository.create_order.return_value = new_order

    # Execute
    result = await order_service.create_order({**order_data, "items": items_data})

    # Assert
    assert result.id == "order1"
    order_service.repository.create_order.assert_called_once_with(order_data, items_data)
    
    # Verify that the Kafka event was sent
    mock_kafka_producer.send_event.assert_called_once()
    call_args = mock_kafka_producer.send_event.call_args[0]
    assert call_args[0] == 'order_created'
    assert call_args[1]['order_id'] == 'order1'

@pytest.mark.asyncio
async def test_create_order_db_failure(order_service, mock_kafka_producer):
    # Setup
    order_data = {"user_id": "user123", "total_amount": 150.50}
    items_data = [{"product_id": "prod1", "quantity": 2, "price_at_purchase": 75.25}]
    
    # Simulate a database error during creation
    order_service.repository.create_order.side_effect = Exception("DB connection failed")

    # Execute and Assert
    with pytest.raises(HTTPException) as excinfo:
        await order_service.create_order({**order_data, "items": items_data})
    
    assert excinfo.value.status_code == 500
    assert "Could not create order" in str(excinfo.value.detail)
    
    # Ensure that if the DB fails, no Kafka event is sent
    mock_kafka_producer.send_event.assert_not_called()

@pytest.mark.asyncio
async def test_create_order_kafka_failure(order_service, mock_kafka_producer):
    # Setup
    order_data = {"user_id": "user123", "total_amount": 150.50}
    items_data = [{"product_id": "prod1", "quantity": 2, "price_at_purchase": 75.25}]
    
    new_order = Order(id="order1", **order_data)
    new_order.items = []
    order_service.repository.create_order.return_value = new_order
    
    # Simulate a Kafka error after the DB write
    mock_kafka_producer.send_event.side_effect = Exception("Kafka is down")

    # Execute and Assert
    # The exception from the producer should propagate up
    with pytest.raises(Exception) as excinfo:
        await order_service.create_order({**order_data, "items": items_data})
        
    assert "Kafka is down" in str(excinfo.value)
    
    # Verify the DB call was still made
    order_service.repository.create_order.assert_called_once()
