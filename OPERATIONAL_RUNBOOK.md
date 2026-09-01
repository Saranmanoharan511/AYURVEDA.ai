# Operational Runbook - Ayurveda-AI Platform

## Overview

This runbook provides operational procedures for managing the Ayurveda-AI platform in production. It covers deployment, monitoring, troubleshooting, backup, recovery, and maintenance procedures.

**Important:** This runbook is designed for use after Sprint 8 when infrastructure (AWS, Neon) has been deployed. Some procedures reference infrastructure that does not yet exist.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Deployment Procedures](#deployment-procedures)
3. [Monitoring and Alerting](#monitoring-and-alerting)
4. [Backup and Recovery](#backup-and-recovery)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance Procedures](#maintenance-procedures)
7. [Security Procedures](#security-procedures)
8. [Emergency Procedures](#emergency-procedures)

---

## System Architecture

### Components

- **Frontend**: React + Vite, deployed on AWS Amplify
- **Backend**: FastAPI, deployed on AWS Lightsail (Docker container)
- **Database**: Neon PostgreSQL with pgvector extension
- **Document Storage**: AWS S3
- **Message Queue**: AWS SQS
- **Email Service**: AWS SES
- **Authentication**: AWS Cognito
- **AI Service**: AWS Bedrock with Guardrails
- **Monitoring**: AWS CloudWatch
- **Workers**: Docker containers for document processing and email sending

### Infrastructure Diagram

```
┌─────────────────┐
│   AWS Amplify   │ (Frontend)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  AWS Lightsail  │ (Backend API)
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌──────┐  ┌──────┐
│ Neon │  │  S3  │
│  DB  │  └──────┘
└──┬───┘       │
   │           ↓
   │      ┌──────┐
   │      │ SQS  │
   │      └──┬───┘
   │         │
   │    ┌────┴────┐
   │    ↓         ↓
   │ ┌──────┐  ┌──────┐
   │ │ Bedrock│ │ SES  │
   │ └──────┘  └──────┘
   │
   ↓
┌──────┐
│Cognito│
└──────┘
```

---

## Deployment Procedures

### Backend Deployment (Lightsail)

#### Prerequisites
- Docker installed on deployment machine
- AWS Lightsail instance provisioned
- Environment variables configured
- Database migrations run

#### Deployment Steps

1. **Build Docker Image**
   ```bash
   cd backend
   docker build -t ayurveda-backend:latest .
   ```

2. **Tag Image for Registry**
   ```bash
   docker tag ayurveda-backend:latest <registry>/ayurveda-backend:latest
   ```

3. **Push to Registry**
   ```bash
   docker push <registry>/ayurveda-backend:latest
   ```

4. **Deploy to Lightsail**
   ```bash
   # SSH into Lightsail instance
   ssh ubuntu@<lightsail-ip>
   
   # Pull latest image
   docker pull <registry>/ayurveda-backend:latest
   
   # Stop existing container
   docker stop ayurveda-backend
   
   # Remove old container
   docker rm ayurveda-backend
   
   # Run new container
   docker run -d \
     --name ayurveda-backend \
     --env-file .env.production \
     -p 8000:8000 \
     <registry>/ayurveda-backend:latest
   ```

5. **Verify Deployment**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

#### Rollback Procedure

If deployment fails:

1. **Stop New Container**
   ```bash
   docker stop ayurveda-backend
   docker rm ayurveda-backend
   ```

2. **Start Previous Version**
   ```bash
   docker run -d \
     --name ayurveda-backend \
     --env-file .env.production \
     -p 8000:8000 \
     <registry>/ayurveda-backend:<previous-tag>
   ```

3. **Verify Rollback**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

### Frontend Deployment (Amplify)

#### Deployment Steps

1. **Build Frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy via Amplify CLI**
   ```bash
   amplify publish
   ```

3. **Verify Deployment**
   - Access the Amplify URL
   - Check console for errors
   - Test critical user flows

### Worker Deployment

#### Document Processing Worker

1. **Build Worker Image**
   ```bash
   cd backend/workers/document_processor
   docker build -t document-worker:latest .
   ```

2. **Deploy to Lightsail/ECS**
   ```bash
   # Similar to backend deployment
   docker run -d \
     --name document-worker \
     --env-file .env.production \
     <registry>/document-worker:latest
   ```

#### Email Worker

1. **Build Worker Image**
   ```bash
   cd backend/workers/email_worker
   docker build -t email-worker:latest .
   ```

2. **Deploy to Lightsail/ECS**
   ```bash
   docker run -d \
     --name email-worker \
     --env-file .env.production \
     <registry>/email-worker:latest
   ```

### Database Migrations

#### Running Migrations

1. **Backup Database**
   ```bash
   # Neon backup via console or API
   ```

2. **Run Migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Verify Migration**
   ```bash
   alembic current
   ```

#### Rollback Migration

```bash
alembic downgrade -1
```

---

## Monitoring and Alerting

### CloudWatch Metrics

#### Key Metrics to Monitor

**Backend API**
- Request count
- Error rate (4xx, 5xx)
- Latency (p50, p95, p99)
- CPU utilization
- Memory utilization
- Disk usage

**Database (Neon)**
- Connection count
- Query latency
- Storage usage
- CPU utilization

**Workers**
- Queue depth (SQS)
- Processing rate
- Error rate
- Worker health

**S3**
- Request count
- Error rate
- Storage usage

### CloudWatch Alarms

#### Pre-configured Alarms

**Error Rate Alarm**
- Metric: API Error Rate
- Threshold: > 5% for 5 minutes
- Action: Send SNS notification

**Latency Alarm**
- Metric: API Latency p95
- Threshold: > 2000ms for 5 minutes
- Action: Send SNS notification

**Queue Depth Alarm**
- Metric: SQS Queue Depth
- Threshold: > 100 messages for 10 minutes
- Action: Send SNS notification

**Database Connection Alarm**
- Metric: Database Connection Count
- Threshold: > 80% of max connections
- Action: Send SNS notification

### Log Monitoring

#### CloudWatch Logs

**Backend Logs**
- Location: `/ayurveda-ai/backend`
- Retention: 30 days
- Key patterns to monitor:
  - ERROR, CRITICAL log levels
  - Database connection failures
  - API timeout errors
  - Authorization failures

**Worker Logs**
- Location: `/ayurveda-ai/workers`
- Retention: 30 days
- Key patterns to monitor:
  - Processing failures
  - Queue errors
  - Retry attempts

### Health Checks

#### API Health Check

```bash
curl http://<backend-url>/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-08-11T12:00:00Z"
}
```

#### AI Service Health Check

```bash
curl http://<backend-url>/api/v1/ai/health
```

Expected response:
```json
{
  "status": "healthy",
  "bedrock_available": true,
  "guardrails_available": true,
  "timestamp": "2026-08-11T12:00:00Z"
}
```

---

## Backup and Recovery

### Database Backup (Neon)

#### Automated Backups

Neon provides automated backups:
- **Frequency**: Daily
- **Retention**: 7 days
- **Point-in-time Recovery**: 7 days

#### Manual Backup

```bash
# Via Neon console or API
# Export database to SQL file
pg_dump <database-url> > backup.sql
```

#### Restore from Backup

```bash
# Restore from SQL file
psql <database-url> < backup.sql
```

#### Point-in-Time Recovery

1. Access Neon console
2. Select database
3. Choose restore point
4. Initiate recovery

### S3 Backup

#### Versioning

S3 bucket has versioning enabled for document storage.

#### Cross-Region Replication

Configure cross-region replication for disaster recovery.

### Application Configuration Backup

#### Environment Variables

- Store environment variables in secure location (AWS Secrets Manager)
- Maintain version control of .env.example files
- Document all required variables

#### Code Backup

- Code is stored in Git repository
- Use Git tags for release versions
- Maintain branches for different environments

---

## Troubleshooting

### Common Issues

#### Backend API Not Responding

**Symptoms**
- Health check fails
- 502/503 errors
- High latency

**Troubleshooting Steps**

1. **Check Container Status**
   ```bash
   docker ps | grep ayurveda-backend
   ```

2. **Check Container Logs**
   ```bash
   docker logs ayurveda-backend --tail 100
   ```

3. **Check Resource Usage**
   ```bash
   docker stats ayurveda-backend
   ```

4. **Restart Container**
   ```bash
   docker restart ayurveda-backend
   ```

5. **Check Database Connectivity**
   ```bash
   # Test database connection from container
   docker exec ayurveda-backend python -c "from app.db.session import engine; engine.connect()"
   ```

#### Database Connection Errors

**Symptoms**
- Database connection timeout
- Connection pool exhausted
- High connection count

**Troubleshooting Steps**

1. **Check Database Status**
   - Access Neon console
   - Check database health
   - Verify connection limits

2. **Check Connection Pool Settings**
   - Review `DATABASE_POOL_SIZE` in .env
   - Adjust if necessary

3. **Check Network Connectivity**
   ```bash
   # Test connectivity from backend to Neon
   docker exec ayurveda-backend ping <neon-host>
   ```

4. **Restart Backend**
   ```bash
   docker restart ayurveda-backend
   ```

#### Worker Not Processing Messages

**Symptoms**
- Queue depth increasing
- No processing logs
- Worker status unhealthy

**Troubleshooting Steps**

1. **Check Worker Status**
   ```bash
   docker ps | grep worker
   ```

2. **Check Worker Logs**
   ```bash
   docker logs document-worker --tail 100
   ```

3. **Check SQS Queue**
   - Access SQS console
   - Check queue depth
   - Check for DLQ messages

4. **Restart Worker**
   ```bash
   docker restart document-worker
   ```

5. **Check SQS Permissions**
   - Verify worker has SQS access
   - Check IAM roles

#### S3 Upload/Download Failures

**Symptoms**
- Pre-signed URL generation fails
- Upload/download errors
- Permission denied

**Troubleshooting Steps**

1. **Check S3 Bucket Status**
   - Access S3 console
   - Verify bucket exists
   - Check bucket policy

2. **Check IAM Permissions**
   - Verify backend has S3 access
   - Check bucket policy allows access

3. **Check Pre-signed URL Expiration**
   - Verify expiration time is reasonable
   - Check system time is correct

4. **Test S3 Access**
   ```bash
   aws s3 ls s3://<bucket-name>
   ```

#### AI Service Failures

**Symptoms**
- AI chat not responding
- Bedrock errors
- Guardrails failures

**Troubleshooting Steps**

1. **Check Bedrock Status**
   - Access AWS console
   - Check Bedrock service health
   - Verify model availability

2. **Check Guardrails Status**
   - Verify guardrail ID is correct
   - Check guardrail configuration

3. **Check API Quotas**
   - Verify Bedrock quota limits
   - Check usage metrics

4. **Check Backend Logs**
   ```bash
   docker logs ayurveda-backend | grep -i bedrock
   ```

#### Frontend Build Failures

**Symptoms**
- Build errors
- Deployment failures
- Runtime errors

**Troubleshooting Steps**

1. **Check Build Logs**
   - Access Amplify console
   - Review build logs
   - Identify error messages

2. **Local Build Test**
   ```bash
   cd frontend
   npm run build
   ```

3. **Check Dependencies**
   ```bash
   npm audit
   npm install
   ```

4. **Check Environment Variables**
   - Verify all required variables are set
   - Check Amplify environment configuration

---

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily

- Review CloudWatch alarms
- Check error logs
- Verify queue depths
- Monitor resource usage

#### Weekly

- Review system performance metrics
- Check database storage usage
- Verify backup completion
- Review security logs

#### Monthly

- Review and update dependencies
- Test disaster recovery procedures
- Review and optimize queries
- Update documentation

### Dependency Updates

#### Backend Dependencies

1. **Check for Updates**
   ```bash
   cd backend
   pip list --outdated
   ```

2. **Update Dependencies**
   ```bash
   pip install --upgrade <package>
   ```

3. **Test Updates**
   ```bash
   pytest tests/
   ```

4. **Deploy to Staging**
   - Deploy to staging environment
   - Run integration tests
   - Monitor for issues

5. **Deploy to Production**
   - Schedule maintenance window
   - Deploy to production
   - Monitor for issues

#### Frontend Dependencies

1. **Check for Updates**
   ```bash
   cd frontend
   npm outdated
   ```

2. **Update Dependencies**
   ```bash
   npm update
   ```

3. **Test Updates**
   ```bash
   npm run test
   npm run build
   ```

4. **Deploy to Staging**
   - Deploy to staging environment
   - Run integration tests
   - Monitor for issues

5. **Deploy to Production**
   - Deploy to production
   - Monitor for issues

### Database Maintenance

#### Index Optimization

1. **Identify Slow Queries**
   - Review CloudWatch metrics
   - Check query logs
   - Use EXPLAIN ANALYZE

2. **Add or Update Indexes**
   ```sql
   CREATE INDEX idx_name ON table_name(column_name);
   ```

3. **Monitor Performance**
   - Check query latency
   - Verify index usage

#### Vacuum and Analyze

Neon handles vacuum automatically, but manual vacuum may be needed:

```sql
VACUUM ANALYZE table_name;
```

---

## Security Procedures

### Security Audits

#### Regular Security Checks

- Review IAM policies
- Check for unused credentials
- Review S3 bucket policies
- Verify security group rules
- Check for open ports

#### Dependency Vulnerability Scanning

```bash
# Backend
pip-audit

# Frontend
npm audit
```

### Incident Response

#### Security Incident Procedure

1. **Identify Incident**
   - Monitor alerts
   - Review logs
   - Assess impact

2. **Contain Incident**
   - Isolate affected systems
   - Block malicious IPs
   - Disable compromised accounts

3. **Eradicate Threat**
   - Remove malware
   - Patch vulnerabilities
   - Update credentials

4. **Recover Systems**
   - Restore from clean backups
   - Verify system integrity
   - Monitor for recurrence

5. **Post-Incident Review**
   - Document incident
   - Update procedures
   - Implement improvements

### Access Control

#### User Access Management

- Regularly review user access
- Remove unused accounts
- Enforce password policies
- Enable MFA where possible

#### API Key Rotation

- Rotate API keys regularly
- Use temporary credentials
- Store keys securely
- Monitor key usage

---

## Emergency Procedures

### Service Outage

#### Complete Backend Outage

1. **Assess Impact**
   - Determine affected services
   - Estimate downtime
   - Communicate with stakeholders

2. **Restore Service**
   - Check infrastructure status
   - Restart containers if needed
   - Restore from backup if needed

3. **Verify Recovery**
   - Run health checks
   - Test critical flows
   - Monitor for issues

4. **Post-Outage Review**
   - Document root cause
   - Update procedures
   - Implement preventive measures

### Data Loss

#### Database Corruption

1. **Stop Writes**
   - Put application in maintenance mode
   - Stop all write operations

2. **Assess Damage**
   - Identify corrupted data
   - Determine extent of loss

3. **Restore from Backup**
   - Select appropriate backup
   - Restore database
   - Verify data integrity

4. **Resume Operations**
   - Take application out of maintenance
   - Monitor for issues
   - Communicate with users

### Security Breach

#### Unauthorized Access

1. **Immediate Actions**
   - Change all credentials
   - Revoke compromised access
   - Enable additional monitoring

2. **Investigate**
   - Review access logs
   - Identify affected data
   - Determine breach scope

3. **Remediate**
   - Patch vulnerabilities
   - Implement additional controls
   - Notify affected parties if required

4. **Prevent Recurrence**
   - Update security policies
   - Conduct security audit
   - Train staff

---

## Contact Information

### Emergency Contacts

- **Primary Admin**: [Contact details]
- **Database Admin**: [Contact details]
- **Security Team**: [Contact details]
- **AWS Support**: [AWS Support details]

### Service Providers

- **AWS Support**: https://aws.amazon.com/support/
- **Neon Support**: https://neon.tech/support/
- **Amplify Support**: https://docs.amplify.aws/

---

## Appendix

### Useful Commands

#### Docker Commands

```bash
# List running containers
docker ps

# View container logs
docker logs <container-name>

# Stop container
docker stop <container-name>

# Restart container
docker restart <container-name>

# Execute command in container
docker exec -it <container-name> bash

# View container stats
docker stats <container-name>
```

#### AWS CLI Commands

```bash
# List S3 buckets
aws s3 ls

# List SQS queues
aws sqs list-queues

# View CloudWatch logs
aws logs tail /ayurveda-ai/backend --follow

# Describe EC2/Lightsail instances
aws lightsail get-instances
```

#### Database Commands

```bash
# Connect to database
psql <database-url>

# Run migration
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View current migration version
alembic current
```

### Documentation Links

- [AWS Documentation](https://docs.aws.amazon.com/)
- [Neon Documentation](https://neon.tech/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Docker Documentation](https://docs.docker.com/)

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-08-11 | 1.0 | Initial runbook created during Sprint 8 | Development Team |

---

**Note:** This runbook is a living document and should be updated as the system evolves and new procedures are established.
