# SSP Order Service

This service is the core transaction engine of the Smart Shop Platform. It handles the complex logic of order creation, coordinates the "Saga pattern" across multiple microservices via Kafka, and stores the canonical state of all orders.

## Core Responsibilities & Features

1.  **Order Creation & State Management:**
    *   Provides API endpoints for clients to place new orders.
    *   Persists order details (items, total amount, status) in a PostgreSQL database using SQLAlchemy.
    *   Maintains the order state machine (e.g., `PENDING` -> `CONFIRMED` -> `SHIPPED` or `PAYMENT_FAILED`).

2.  **Event-Driven Coordination (Saga Pattern):**
    *   When an order is created, the service does *not* synchronously call the inventory or payment services.
    *   Instead, it immediately returns a `PENDING` response to the user and publishes an `order_created` event to an **Amazon MSK (Kafka)** topic.
    *   Other services (Inventory, Recommender) listen for this event and react asynchronously, decoupling the system and increasing fault tolerance.

3.  **Database Migrations:**
    *   Uses **Alembic** to manage changes to the database schema over time, ensuring the database structure is version-controlled alongside the application code.

## Architecture
- **Framework:** **FastAPI**
- **Database:** **PostgreSQL** (provisioned via Amazon RDS).
- **Event Bus:** **Kafka** (provisioned via Amazon MSK or self-managed EC2).
- **Deployment:** **AWS ECS Fargate**
- **Dependencies:**
    - `SQLAlchemy` & `asyncpg`: For asynchronous database operations.
    - `alembic`: For database migrations.
    - `kafka-python-ng`: For publishing events to Kafka.
    - `boto3`: To fetch database and Kafka endpoints from AWS SSM.

## Local Development

1.  Create a virtual environment: `python3 -m venv venv`
2.  Activate it: `source venv/bin/activate`
3.  Install dependencies: `pip install -r requirements.txt` and `pip install -r requirements-dev.txt`
4.  **Set Up Local Infrastructure:** This service requires PostgreSQL and Kafka.
    *   *PostgreSQL:* `docker run --name ssp-postgres-order -e POSTGRES_PASSWORD=password -e POSTGRES_DB=ssp_orders -p 5432:5432 -d postgres`
    *   *Kafka:* Using a docker-compose file for Kafka/Zookeeper is recommended for local dev.
5.  **Run Migrations:** Apply the database schema:
    ```bash
    alembic upgrade head
    ```
6.  Run the application:
    ```bash
    uvicorn app.main:app --reload --port 8003
    ```
