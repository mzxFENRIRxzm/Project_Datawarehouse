-- =============================================================================
-- PostgreSQL Init: Create additional databases for Airflow & Superset metadata
-- This script runs automatically on first container startup
-- =============================================================================

-- Airflow metadata database
SELECT 'CREATE DATABASE airflow_meta'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow_meta')\gexec

-- Superset metadata database
SELECT 'CREATE DATABASE superset_meta'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'superset_meta')\gexec

-- Hive Metastore database for the integrated Lakehouse services
SELECT 'CREATE DATABASE metastore'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metastore')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE airflow_meta TO suphasan;
GRANT ALL PRIVILEGES ON DATABASE superset_meta TO suphasan;
GRANT ALL PRIVILEGES ON DATABASE metastore TO suphasan;
