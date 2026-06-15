import pytest
from unittest.mock import patch, AsyncMock

# We use the client fixture from conftest.py which uses an in-memory SQLite DB
def test_create_order_api_success(client, mock_kafka_producer):
    # Setup
    order_payload = {
        "user_id": "user_api_1",
        "total_amount": 120.0,
        "items": [
            {"product_id": "prod_api_1", "quantity": 1, "price_at_purchase": 120.0}
        ]
    }

    # Execute
    response = client.post("/api/v1/orders", json=order_payload)

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["message"] == "Order created successfully"
    assert "order_id" in response_data
    
    # Verify that the Kafka producer was called
    mock_kafka_producer.send.assert_called_once()
    call_args = mock_kafka_producer.send.call_args[0]
    assert call_args[0] == 'order_created' # Topic
    assert call_args[1]['user_id'] == 'user_api_1' # Message content

def test_create_order_api_bad_payload(client):
    # Setup with missing 'items'
    order_payload = {
        "user_id": "user_api_2",
        "total_amount": 120.0
    }

    # Execute
    response = client.post("/api/v1/orders", json=order_payload)

    # Assert
    assert response.status_code == 422 # FastAPI's Unprocessable Entity
    assert "items" in response.text
    assert "Field required" in response.text

def test_create_order_api_db_failure(client, mock_kafka_producer):
    # Mock the service layer to simulate a DB failure
    with patch("app.api.order_routes.OrderService.create_order", new_callable=AsyncMock) as mock_create:
        from fastapi import HTTPException
        mock_create.side_effect = HTTPException(status_code=500, detail="Could not create order.")
        
        order_payload = {
            "user_id": "user_api_3",
            "total_amount": 100.0,
            "items": []
        }
        
        response = client.post("/api/v1/orders", json=order_payload)
        
        assert response.status_code == 500
        assert "Could not create order" in response.text
        
        # Ensure Kafka was not called if the DB write failed
        mock_kafka_producer.send.assert_not_called()
