import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.core.database import get_db, Base, engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

async def override_get_db():
    """Dependency override to use the test database."""
    async with TestingSessionLocal() as session:
        yield session

# Apply the override for the app's dependency
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
async def db_session():
    """Provides a test database session and handles setup/teardown."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
def client():
    """Provides a TestClient for the FastAPI app."""
    return TestClient(app)

@pytest.fixture(scope="function")
def mock_kafka_producer():
    """Mocks the Kafka producer service."""
    with patch("app.events.kafka_producer.KafkaProducer") as MockKafka:
        mock_producer_instance = MagicMock()
        MockKafka.return_value = mock_producer_instance

        # Also patch the singleton instance if it was created
        with patch("app.events.kafka_producer.kafka_producer_service.producer", mock_producer_instance):
            yield mock_producer_instance
