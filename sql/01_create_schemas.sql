-- ============================================================================
-- 01_create_schemas.sql
-- Hospital Readmission Analytics Database - Schema Initialization
-- ============================================================================

-- Metadata Schema: Pipeline audit, file checksums, ingestion logs
CREATE SCHEMA IF NOT EXISTS metadata;

-- Staging Schema: Raw ingested tables preserving original source representations
CREATE SCHEMA IF NOT EXISTS staging;

-- Rejected Schema: Records rejected by data quality rules with audit reasons
CREATE SCHEMA IF NOT EXISTS rejected;

-- Curated Schema: Standardized, deduplicated, privacy-safe relational entities
CREATE SCHEMA IF NOT EXISTS curated;

-- Analytics Schema: Pre-aggregated data marts, summary tables, and KPIs
CREATE SCHEMA IF NOT EXISTS analytics;
