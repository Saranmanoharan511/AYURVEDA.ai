# Neon PostgreSQL Backup and Recovery Configuration

## Overview

This document defines the backup and recovery strategy for the Neon PostgreSQL database used by the Ayurveda AI Platform. Neon provides automated backups, point-in-time recovery (PITR), and branching capabilities that ensure data durability and enable rapid recovery scenarios.

## Neon Backup Features

### 1. Automated Backups

Neon automatically creates continuous backups of your database with the following characteristics:

- **Frequency**: Continuous WAL (Write-Ahead Log) archiving
- **Retention**: Configurable retention period (default: 7 days)
- **Storage**: Compressed and encrypted at rest
- **Availability**: Backups are stored in multiple availability zones

### 2. Point-in-Time Recovery (PITR)

Neon supports point-in-time recovery to any point within the retention window:

- **Granularity**: Recovery to any second within the retention period
- **Speed**: Typically completes within minutes depending on data volume
- **Consistency**: Ensures transactional consistency at the recovery point

### 3. Database Branching

Neon's branching feature enables:

- **Zero-copy branching**: Create instant database copies without duplicating storage
- **Development environments**: Isolated development and testing branches
- **Data isolation**: Separate branches for different environments (dev, staging, prod)
- **Merge capabilities**: Promote branches to production when needed

## Recommended Backup Configuration

### Retention Policy

```yaml
# Recommended retention settings
backup_retention_days: 30  # Extended retention for healthcare data
point_in_time_recovery: true
min_retention_days: 7      # Minimum retention (Neon default)
max_retention_days: 90     # Maximum retention for compliance
```

### Backup Schedule

Neon handles backup scheduling automatically, but you should configure:

1. **Continuous WAL Archiving**: Enabled by default
2. **Base Backups**: Automatic daily base backups
3. **Retention Period**: Configure based on compliance requirements

### Configuration via Neon Console

1. Navigate to your Neon project
2. Select the database branch
3. Go to "Settings" > "Backup"
4. Configure retention period
5. Enable point-in-time recovery

## Recovery Procedures

### Scenario 1: Point-in-Time Recovery

**Use Case**: Recover from accidental data deletion or corruption

**Steps**:

1. Identify the recovery point timestamp
   ```bash
   # Example: Recover to 2026-08-10 14:30:00 UTC
   RECOVERY_TIMESTAMP="2026-08-10T14:30:00Z"
   ```

2. Create a new branch from the recovery point
   ```bash
   # Using Neon CLI
   neon branches create recovery-branch \
     --parent-id ayurveda-ai-prod \
     --timestamp $RECOVERY_TIMESTAMP
   ```

3. Verify data integrity
   ```sql
   -- Connect to recovery branch
   -- Run validation queries
   SELECT COUNT(*) FROM patients;
   SELECT COUNT(*) FROM consultations;
   ```

4. Promote recovery branch to production (if needed)
   ```bash
   neon branches promote recovery-branch
   ```

5. Update application configuration to point to new branch

### Scenario 2: Branch for Development

**Use Case**: Create isolated development environment

**Steps**:

1. Create development branch from production
   ```bash
   neon branches create ayurveda-ai-dev \
     --parent-id ayurveda-ai-prod
   ```

2. Configure application to use development branch
   ```env
   DATABASE_URL=postgresql://user:password@dev-project-id.aws.neon.tech/ayurveda_ai_dev?sslmode=require
   ```

3. Develop and test changes in isolation

4. Merge changes back to production via application migrations

### Scenario 3: Emergency Recovery

**Use Case**: Complete database recovery from catastrophic failure

**Steps**:

1. Assess the situation and identify the latest consistent recovery point
2. Create emergency recovery branch
   ```bash
   neon branches create emergency-recovery \
     --parent-id ayurveda-ai-prod \
     --timestamp $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)
   ```
3. Verify all critical data is intact
4. Update DNS/load balancer to point to recovery branch
5. Monitor application health
6. Document the incident and recovery timeline

## Backup Validation

### Automated Validation Checks

Implement the following validation checks:

1. **Backup Existence Check**: Verify backups are being created
   ```python
   def check_backup_status():
       """Verify Neon backup status via API"""
       # Use Neon API to check backup status
       # Alert if no recent backups found
       pass
   ```

2. **Data Integrity Check**: Verify backup data integrity
   ```sql
   -- Run checksum queries on critical tables
   SELECT COUNT(*) FROM patients;
   SELECT COUNT(*) FROM consultations;
   SELECT COUNT(*) FROM audit_logs;
   ```

3. **Recovery Drill**: Periodic recovery drills
   - Schedule monthly recovery drills
   - Create test branch from recent backup
   - Verify data consistency
   - Document recovery time

### Monitoring and Alerts

Configure monitoring for:

1. **Backup Status**: Alert if backups fail
2. **Storage Usage**: Monitor backup storage consumption
3. **Recovery Time**: Track recovery time metrics
4. **Branch Count**: Monitor number of branches to control costs

## Disaster Recovery Plan

### RPO (Recovery Point Objective)

- **Target**: 1 minute (Neon's continuous WAL archiving)
- **Achievable**: < 1 second with Neon's PITR

### RTO (Recovery Time Objective)

- **Target**: 15 minutes
- **Achievable**: 5-10 minutes with Neon branching

### Disaster Recovery Checklist

- [ ] Identify recovery point timestamp
- [ ] Create recovery branch
- [ ] Verify data integrity
- [ ] Update application configuration
- [ ] Test application functionality
- [ ] Switch traffic to recovery branch
- [ ] Monitor system health
- [ ] Document recovery process

## Compliance Considerations

### HIPAA Requirements

1. **Data Backup**: Regular, automated backups
2. **Data Recovery**: Tested recovery procedures
3. **Data Encryption**: Backups encrypted at rest and in transit
4. **Audit Logging**: Log all backup and recovery operations
5. **Retention Period**: Maintain backups for required retention period
6. **Access Controls**: Restrict backup/recovery access to authorized personnel

### GDPR Considerations

1. **Right to Erasure**: Ensure backup deletion capability
2. **Data Portability**: Support data export from backups
3. **Breach Notification**: Monitor for unauthorized backup access
4. **Data Minimization**: Only backup necessary data

## Cost Optimization

### Backup Storage Costs

Neon charges for backup storage based on:

- **Base backup size**: Compressed storage
- **WAL retention**: WAL log storage
- **Branch storage**: Deduplicated storage for branches

### Cost Optimization Strategies

1. **Retention Period**: Balance retention vs. cost
2. **Branch Management**: Delete unused branches
3. **Compression**: Neon automatically compresses backups
4. **Monitoring**: Monitor storage usage regularly

### Cost Monitoring

```python
def monitor_backup_storage():
    """Monitor Neon backup storage costs"""
    # Use Neon API to get storage metrics
    # Alert if costs exceed threshold
    pass
```

## Security Considerations

### Backup Encryption

- **At Rest**: Neon encrypts all backups by default
- **In Transit**: SSL/TLS encryption for all connections
- **Key Management**: Neon manages encryption keys

### Access Control

1. **Role-Based Access**: Restrict backup/recovery operations
2. **API Keys**: Rotate API keys regularly
3. **Audit Logging**: Log all backup/recovery operations
4. **Network Security**: Use VPC endpoints for secure access

### Backup Isolation

- **Separate Projects**: Use separate Neon projects for different environments
- **Branch Isolation**: Use branches for development/testing
- **Network Isolation**: Configure network policies appropriately

## Integration with Application

### Application Configuration

```python
# config.py
class Settings(BaseSettings):
    # Neon Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    NEON_PROJECT_ID: str = os.getenv("NEON_PROJECT_ID")
    NEON_BRANCH_ID: str = os.getenv("NEON_BRANCH_ID", "main")
    
    # Backup Configuration
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    ENABLE_PITR: bool = os.getenv("ENABLE_PITR", "true").lower() == "true"
```

### Backup Health Check Endpoint

```python
@router.get("/health/backup")
async def check_backup_health():
    """Check backup health status"""
    # Query Neon API for backup status
    # Return health status
    pass
```

## Testing and Validation

### Backup Recovery Test Plan

1. **Weekly**: Automated backup existence check
2. **Monthly**: Recovery drill with test branch
3. **Quarterly**: Full disaster recovery simulation
4. **Annually**: Compliance audit of backup procedures

### Test Scenarios

1. **Single Table Recovery**: Recover a single table
2. **Point-in-Time Recovery**: Recover to specific timestamp
3. **Branch Promotion**: Promote branch to production
4. **Emergency Recovery**: Simulate emergency recovery scenario

## Documentation and Training

### Documentation Requirements

1. **Backup Procedures**: Document all backup procedures
2. **Recovery Procedures**: Document all recovery scenarios
3. **Runbooks**: Create runbooks for common recovery scenarios
4. **Training**: Train operations team on backup/recovery procedures

### Training Checklist

- [ ] Backup configuration
- [ ] Recovery procedures
- [ ] Neon CLI usage
- [ ] Monitoring and alerting
- [ ] Incident response

## Post-Sprint 8 Implementation

These backup and recovery configurations must be implemented manually after Sprint 8 completion. The infrastructure team should:

1. **Configure Neon Project**:
   - Create Neon project with appropriate sizing
   - Configure backup retention period
   - Enable point-in-time recovery
   - Set up monitoring and alerts

2. **Implement Backup Validation**:
   - Set up automated backup health checks
   - Configure monitoring for backup status
   - Implement alerting for backup failures

3. **Test Recovery Procedures**:
   - Perform initial recovery drill
   - Document recovery times
   - Validate data integrity after recovery

4. **Configure Branching Strategy**:
   - Set up development branch
   - Configure staging branch
   - Document branch promotion procedures

5. **Update Application Configuration**:
   - Configure application with Neon connection strings
   - Update environment variables
   - Test application connectivity

6. **Document Procedures**:
   - Create runbooks for common scenarios
   - Document contact information for emergencies
   - Train operations team

## Monitoring Metrics

### Key Metrics to Monitor

1. **Backup Status**: Last successful backup time
2. **Storage Usage**: Backup storage consumption
3. **Recovery Time**: Time to complete recovery operations
4. **Branch Count**: Number of active branches
5. **WAL Size**: WAL log size and growth rate

### CloudWatch Integration

```python
def publish_backup_metrics():
    """Publish backup metrics to CloudWatch"""
    # Collect Neon backup metrics
    # Publish to CloudWatch
    pass
```

## Troubleshooting

### Common Issues

1. **Backup Failure**:
   - Check Neon service status
   - Verify project configuration
   - Review error logs

2. **Recovery Failure**:
   - Verify recovery point exists
   - Check branch permissions
   - Review recovery logs

3. **Storage Limit Reached**:
   - Review retention period
   - Delete old branches
   - Contact Neon support for limits increase

## References

- [Neon Documentation](https://neon.tech/docs)
- [Neon Backup and Recovery](https://neon.tech/docs/manage/backups)
- [Neon Branching](https://neon.tech/docs/manage/branches)
- [HIPAA Compliance on Neon](https://neon.tech/docs/compliance/hipaa)
- [GDPR Compliance on Neon](https://neon.tech/docs/compliance/gdpr)
