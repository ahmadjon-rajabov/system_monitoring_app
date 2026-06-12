import pytest
import os
from testcontainers.postgres import PostgresContainer
from src.database import DatabaseManager

@pytest.fixture(scope="module")
def postgres_db():
    print("\n[Setup] Spinning up temporary PostgreSQL Docker container...")

    with PostgresContainer("postgres:15-alpine") as postgres:
        os.environ["POSTGRES_HOST"] = postgres.get_container_host_ip()
        os.environ["POSTGRES_PORT"] = str(postgres.get_exposed_port(5432))
        os.environ["POSTGRES_DB"] = postgres.dbname
        os.environ["POSTGRES_USER"] = postgres.username
        os.environ["POSTGRES_PASSWORD"] = postgres.password

        yield postgres

        print("\n[Teardown] Destroying temporary PostgreSQL container...")

def test_database_metrics_pipeline(postgres_db):
    """
    E2E Data Pipeline Test: 
    Proves the SystemMonitor can write to a real DB, and the AutoScaler can read from it
    """
    db = DatabaseManager()

    print("\nWriting metric to real database...")
    db.save_metric(cpu=50.0, memory=60.0, disk=40.0, network=3.5)

    print("Reading metric from real database...")
    metrics = db.get_recent_metrics(limit=1)

    assert len(metrics) == 1, "Database record matched"
    assert metrics[0]['network'] == 3.5, "Network traffic matched"
    assert metrics[0]['cpu'] == 50.0, "CPU mached"