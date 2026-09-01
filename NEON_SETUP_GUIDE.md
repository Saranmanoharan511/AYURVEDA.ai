# Neon PostgreSQL Setup Guide (Post-Sprint 8)

## Overview

This document provides step-by-step instructions for setting up Neon PostgreSQL database for the Ayurveda-AI platform. These procedures are to be executed after Sprint 8 when infrastructure deployment begins.

**Important:** This guide is for post-Sprint 8 infrastructure integration. Do not execute these steps during Sprint 8.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Neon Account Setup](#neon-account-setup)
3. [Project Creation](#project-creation)
4. [Database Creation](#database-creation)
5. [pgvector Extension Setup](#pgvector-extension-setup)
6. [Connection Configuration](#connection-configuration)
7. [Database Migrations](#database-migrations)
8. [Backup Configuration](#backup-configuration)
9. [Security Configuration](#security-configuration)
10. [Monitoring Configuration](#monitoring-configuration)

---

## Prerequisites

### Neon Account

- Neon account created at https://neon.tech
- Payment method configured (if using paid tier)
- Neon CLI installed (optional but recommended)

### Required Information

- Project name
- Database name
- Region selection
- Compute size
- Storage size

### Naming Convention

Use consistent naming convention:
- Project: `ayurveda-ai-prod`
- Database: `ayurveda_ai`
- Branch: `main` (production), `staging` (staging)

---

## Neon Account Setup

#### 1. Create Neon Account

1. Navigate to https://neon.tech
2. Click "Sign Up"
3. Sign up with GitHub, Google, or email
4. Verify email address
5. Complete onboarding

#### 2. Configure Payment Method (if needed)

1. Navigate to Settings > Billing
2. Add payment method
3. Select plan (Free, Pro, or Enterprise)
4. Configure billing alerts

#### 3. Install Neon CLI (Optional)

```bash
# Using npm
npm install -g neonctl

# Using homebrew (macOS)
brew install neon/tap/neonctl

# Verify installation
neonctl --version
```

---

## Project Creation

#### 1. Create Project via Console

1. Navigate to Neon Console
2. Click "Create a project"
3. Enter project details:
   - Name: `ayurveda-ai-prod`
   - Region: Select closest to your users (e.g., us-east-1)
   - PostgreSQL version: 15 (latest stable)
   - Compute size: Start with 0.25 CPU, 1 GB RAM
   - Storage: Start with 20 GB
4. Click "Create project"

#### 2. Create Project via CLI

```bash
neonctl projects create \
  --name ayurveda-ai-prod \
  --region us-east-1 \
  --pg-version 15
```

#### 3. Save Project Details

Save the following information:
- Project ID
- Connection string
- API key (if using API)

---

## Database Creation

#### 1. Create Database

Neon automatically creates a default database named `neondb`. Create a new database:

```sql
CREATE DATABASE ayurveda_ai;
```

Or via CLI:

```bash
neonctl databases create ayurveda-ai-prod --name ayurveda_ai
```

#### 2. Create Additional Databases (if needed)

```sql
-- Staging database
CREATE DATABASE ayurveda_ai_staging;

-- Testing database
CREATE DATABASE ayurveda_ai_test;
```

#### 3. Verify Database Creation

```bash
neonctl databases list ayurveda-ai-prod
```

---

## pgvector Extension Setup

#### 1. Enable pgvector Extension

Connect to the database:

```bash
psql postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai
```

Enable the extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 2. Verify Extension

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

Expected output:
```
 extname | extowner | extnamespace | extrelocatable | extversion | extconfig | extcondition
---------+----------+--------------+----------------+------------+-----------+--------------
 vector  |      10 |         2200 | f              | 0.5.0      |           |
```

#### 3. Test pgvector Functionality

```sql
-- Create a test table with vector column
CREATE TABLE test_vectors (
    id SERIAL PRIMARY KEY,
    embedding vector(1536)
);

-- Insert test vector
INSERT INTO test_vectors (embedding) VALUES ('[0.1,0.2,0.3,...]');

-- Query vector
SELECT * FROM test_vectors;

-- Clean up
DROP TABLE test_vectors;
```

---

## Connection Configuration

#### 1. Get Connection String

From Neon Console:
1. Select project
2. Click "Connection Details"
3. Copy connection string

Connection string format:
```
postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai?sslmode=require
```

#### 2. Configure Backend Connection

Update backend `.env.production`:

```bash
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai?sslmode=require
```

#### 3. Configure Connection Pooling

Neon provides connection pooling. Use pooling connection string:

```
postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai?sslmode=require&pgbouncer=true
```

#### 4. Test Connection

```bash
# Using psql
psql $DATABASE_URL

# Using Python
python -c "from app.db.session import engine; engine.connect()"
```

---

## Database Migrations

#### 1. Configure Alembic for Neon

Update `alembic.ini`:

```ini
sqlalchemy.url = postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai?sslmode=require
```

#### 2. Run Migrations

```bash
cd backend
alembic upgrade head
```

#### 3. Verify Migration

```bash
alembic current
```

Expected output: Current revision(s)

#### 4. Create Branch for Staging

Neon supports branching. Create staging branch:

```bash
neonctl branches create ayurveda-ai-prod --name staging
```

#### 5. Run Migrations on Staging

```bash
# Update DATABASE_URL to point to staging branch
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai?sslmode=require&branch=staging

alembic upgrade head
```

---

## Backup Configuration

#### 1. Configure Automated Backups

Neon provides automated backups:
- **Point-in-Time Recovery (PITR)**: 7 days retention
- **Automated backups**: Daily

Configure via Console:
1. Navigate to project settings
2. Configure backup retention
3. Set backup schedule (if using paid tier)

#### 2. Manual Backup

Export database:

```bash
pg_dump $DATABASE_URL > backup.sql
```

#### 3. Restore from Backup

```bash
psql $DATABASE_URL < backup.sql
```

#### 4. Point-in-Time Recovery

Via Console:
1. Navigate to project
2. Select "Time Travel"
3. Choose restore point
4. Create new branch from restore point

#### 5. Backup Verification

Regularly test backup restoration:
1. Create test branch
2. Restore backup to test branch
3. Verify data integrity
4. Delete test branch

---

## Security Configuration

#### 1. Configure Network Access

Neon allows IP-based access control:

Via Console:
1. Navigate to project settings
2. Configure allowed IP ranges
3. Add backend server IP
4. Add development IP (if needed)

#### 2. Configure SSL/TLS

Neon enforces SSL by default. Verify:

```bash
psql "postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai?sslmode=require"
```

#### 3. Rotate Database Password

Via Console:
1. Navigate to project settings
2. Reset password
3. Update application configuration
4. Restart application

#### 4. Configure Row-Level Security (Optional)

For additional security, configure RLS:

```sql
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

CREATE POLICY patient_isolation ON patients
  FOR ALL
  TO authenticated_user
  USING (user_id = current_user_id());
```

---

## Monitoring Configuration

#### 1. Enable Query Insights

Neon provides query insights for monitoring:

Via Console:
1. Navigate to project
2. Enable Query Insights
3. Configure retention period
4. Set up alerts

#### 2. Monitor Connection Usage

Via Console:
1. Navigate to project
2. View connection metrics
3. Monitor connection pool usage
4. Set up alerts for high usage

#### 3. Monitor Storage Usage

Via Console:
1. Navigate to project
2. View storage metrics
3. Monitor growth trends
4. Set up alerts for storage limits

#### 4. Configure CloudWatch Integration (Optional)

Export Neon metrics to CloudWatch:

```bash
# Use Neon API to export metrics
# Configure CloudWatch agent
```

---

## Performance Optimization

#### 1. Configure Compute Size

Based on workload, adjust compute size:

- **Development**: 0.25 CPU, 1 GB RAM
- **Staging**: 0.5 CPU, 2 GB RAM
- **Production**: 1-2 CPU, 4-8 GB RAM

Via Console:
1. Navigate to project settings
2. Adjust compute size
3. Apply changes

#### 2. Configure Connection Pooling

Use Neon's connection pooling:

```bash
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai?sslmode=require&pgbouncer=true
```

#### 3. Optimize Queries

Use Query Insights to identify slow queries:
1. Navigate to Query Insights
2. Review slow queries
3. Add indexes if needed
4. Optimize query structure

#### 4. Configure Indexes

Create indexes for frequently queried columns:

```sql
CREATE INDEX idx_patients_user_id ON patients(user_id);
CREATE INDEX idx_consultations_patient_id ON consultations(patient_id);
CREATE INDEX idx_consultations_doctor_id ON consultations(doctor_id);
CREATE INDEX idx_document_chunks_patient_id ON document_chunks(patient_id);
```

---

## Branch Management

#### 1. Create Development Branch

```bash
neonctl branches create ayurveda-ai-prod --name dev
```

#### 2. Switch Branch in Application

Update DATABASE_URL to use branch:

```bash
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai?sslmode=require&branch=dev
```

#### 3. Merge Branch to Main

Via Console:
1. Navigate to branches
2. Select dev branch
3. Click "Merge to main"
4. Review changes
5. Confirm merge

#### 4. Delete Old Branches

```bash
neonctl branches delete ayurveda-ai-prod --name old-branch
```

---

## Troubleshooting

### Connection Issues

#### Problem: Cannot connect to database

**Solutions**:
1. Verify connection string is correct
2. Check network access configuration
3. Verify SSL is enabled
4. Check if database is running

#### Problem: Connection pool exhausted

**Solutions**:
1. Increase connection pool size
2. Reduce connection timeout
3. Optimize query performance
4. Scale compute resources

### Performance Issues

#### Problem: Slow queries

**Solutions**:
1. Use Query Insights to identify slow queries
2. Add appropriate indexes
3. Optimize query structure
4. Increase compute size

#### Problem: High CPU usage

**Solutions**:
1. Scale compute resources
2. Optimize queries
3. Reduce connection count
4. Review workload patterns

### Storage Issues

#### Problem: Storage nearly full

**Solutions**:
1. Increase storage allocation
2. Archive old data
3. Clean up unused data
4. Optimize data types

### Migration Issues

#### Problem: Migration fails

**Solutions**:
1. Check migration file syntax
2. Verify database connection
3. Rollback to previous version
4. Fix migration and retry

---

## Cost Management

### Pricing Tiers

- **Free**: 0.5 GB storage, 1 branch, limited compute
- **Pro**: $19/month, 8 GB storage, unlimited branches
- **Enterprise**: Custom pricing

### Cost Optimization

1. **Monitor Usage**: Regularly review usage metrics
2. **Clean Up**: Delete unused branches
3. **Archive**: Archive old data to reduce storage
4. **Scale**: Adjust compute size based on workload

### Budget Alerts

Configure budget alerts:
1. Navigate to Neon Console
2. Set budget threshold
3. Configure email notifications
4. Monitor spending

---

## Verification Steps

### 1. Verify Database Connection

```bash
psql $DATABASE_URL -c "SELECT version();"
```

### 2. Verify pgvector Extension

```bash
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### 3. Verify Migrations

```bash
alembic current
```

### 4. Verify Connection Pooling

```bash
# Check connection pool status via Neon Console
```

### 5. Verify Backup

```bash
# Create test backup
pg_dump $DATABASE_URL > test_backup.sql

# Verify backup file
ls -lh test_backup.sql
```

---

## Appendix

### Useful Commands

#### Neon CLI Commands

```bash
# List projects
neonctl projects list

# Get project details
neonctl projects describe ayurveda-ai-prod

# List databases
neonctl databases list ayurveda-ai-prod

# List branches
neonctl branches list ayurveda-ai-prod

# Create branch
neonctl branches create ayurveda-ai-prod --name new-branch

# Delete branch
neonctl branches delete ayurveda-ai-prod --name old-branch
```

#### PostgreSQL Commands

```bash
# Connect to database
psql $DATABASE_URL

# List tables
\dt

# Describe table
\d table_name

# Run query
psql $DATABASE_URL -c "SELECT * FROM table_name;"

# Export database
pg_dump $DATABASE_URL > backup.sql

# Import database
psql $DATABASE_URL < backup.sql
```

### Connection String Formats

#### Standard Connection
```
postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai?sslmode=require
```

#### Connection Pooling
```
postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai?sslmode=require&pgbouncer=true
```

#### Branch-Specific Connection
```
postgresql://user:password@ep-xxx.region.aws.neon.tech/ayurveda_ai?sslmode=require&branch=staging
```

### References

- [Neon Documentation](https://neon.tech/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

---

**Note:** This Neon setup guide should be updated as database requirements evolve and new features are added.
