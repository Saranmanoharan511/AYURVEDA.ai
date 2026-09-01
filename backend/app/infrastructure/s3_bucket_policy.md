# S3 Bucket Policy Documentation

## Overview

This document defines the recommended S3 bucket policies for the Ayurveda AI Platform to ensure secure storage of patient documents and reports. These policies enforce least-privilege access, encryption requirements, and compliance with healthcare data protection standards.

## Bucket Naming Convention

- **Patient Documents Bucket**: `ayurveda-ai-patient-documents-{region}-{account-id}`
- **Reports Bucket**: `ayurveda-ai-reports-{region}-{account-id}`

## Security Principles

1. **Least Privilege**: Grant only necessary permissions
2. **Encryption**: Enforce server-side encryption (SSE-S3 or SSE-KMS)
3. **HTTPS Only**: Block all non-HTTPS requests
4. **Audit Logging**: Enable CloudTrail and S3 access logs
5. **Versioning**: Enable bucket versioning for data recovery
6. **Public Access**: Block all public access

## Recommended Bucket Policy

### Patient Documents Bucket Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedObjectUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::ayurveda-ai-patient-documents-*/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": [
            "AES256",
            "aws:kms"
          ]
        }
      }
    },
    {
      "Sid": "DenyInsecureCommunications",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::ayurveda-ai-patient-documents-*",
        "arn:aws:s3:::ayurveda-ai-patient-documents-*/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    },
    {
      "Sid": "AllowBackendServiceRole",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::{account-id}:role/ayurveda-ai-backend-service-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::ayurveda-ai-patient-documents-*",
        "arn:aws:s3:::ayurveda-ai-patient-documents-*/*"
      ]
    },
    {
      "Sid": "AllowDocumentProcessingWorker",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::{account-id}:role/ayurveda-ai-document-worker-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::ayurveda-ai-patient-documents-*/*"
    },
    {
      "Sid": "AllowTextractService",
      "Effect": "Allow",
      "Principal": {
        "Service": "textract.amazonaws.com"
      },
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::ayurveda-ai-patient-documents-*/*",
      "Condition": {
        "StringEquals": {
          "aws:SourceArn": "arn:aws:iam::{account-id}:role/ayurveda-ai-textract-role"
        }
      }
    }
  ]
}
```

### Reports Bucket Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedObjectUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::ayurveda-ai-reports-*/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": [
            "AES256",
            "aws:kms"
          ]
        }
      }
    },
    {
      "Sid": "DenyInsecureCommunications",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::ayurveda-ai-reports-*",
        "arn:aws:s3:::ayurveda-ai-reports-*/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    },
    {
      "Sid": "AllowBackendServiceRole",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::{account-id}:role/ayurveda-ai-backend-service-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::ayurveda-ai-reports-*",
        "arn:aws:s3:::ayurveda-ai-reports-*/*"
      ]
    },
    {
      "Sid": "AllowDoctorsAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::{account-id}:role/ayurveda-ai-doctor-role"
      },
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::ayurveda-ai-reports-*/*"
    }
  ]
}
```

## Bucket Configuration Requirements

### 1. Block Public Access

```json
{
  "BlockPublicAcls": true,
  "IgnorePublicAcls": true,
  "BlockPublicPolicy": true,
  "RestrictPublicBuckets": true
}
```

### 2. Server-Side Encryption

- **Default Encryption**: AES256 (SSE-S3) or aws:kms (SSE-KMS)
- **KMS Key**: Use customer-managed KMS key for enhanced security
- **Key Rotation**: Enable automatic KMS key rotation

### 3. Versioning

Enable bucket versioning for data recovery and audit purposes:

```bash
aws s3api put-bucket-versioning \
  --bucket ayurveda-ai-patient-documents-{region}-{account-id} \
  --versioning-configuration Status=Enabled
```

### 4. Lifecycle Rules

Implement lifecycle rules for cost optimization:

```json
{
  "Rules": [
    {
      "Id": "TransitionToStandardIA",
      "Status": "Enabled",
      "Filter": {},
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "STANDARD_IA"
        }
      ]
    },
    {
      "Id": "TransitionToGlacier",
      "Status": "Enabled",
      "Filter": {},
      "Transitions": [
        {
          "Days": 365,
          "StorageClass": "GLACIER"
        }
      ]
    },
    {
      "Id": "DeleteOldVersions",
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 365
      }
    }
  ]
}
```

### 5. Access Logging

Enable S3 server access logging:

```bash
aws s3api put-bucket-logging \
  --bucket ayurveda-ai-patient-documents-{region}-{account-id} \
  --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"ayurveda-ai-logs-{region}-{account-id}","TargetPrefix":"s3-access-logs/"}}'
```

### 6. CloudTrail Integration

Ensure CloudTrail is enabled to log all S3 API calls:

```json
{
  "DataEvents": [
    {
      "Type": "AWS::S3::Object",
      "Resources": [
        {
          "Type": "AWS::S3::Object",
          "Values": ["arn:aws:s3:::ayurveda-ai-patient-documents-*/*"]
        }
      ],
      "ReadWriteType": "All"
    }
  ]
}
```

## IAM Role Requirements

### Backend Service Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetObjectVersion"
      ],
      "Resource": [
        "arn:aws:s3:::ayurveda-ai-*",
        "arn:aws:s3:::ayurveda-ai-*/*"
      ]
    }
  ]
}
```

### Document Processing Worker Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::ayurveda-ai-patient-documents-*/*"
      ]
    }
  ]
}
```

## Patient Data Isolation

To ensure patient data isolation, implement the following:

1. **Prefix-based Isolation**: Use patient ID as object key prefix
   - Key pattern: `patients/{patient_id}/documents/{document_id}/{filename}`
   - Key pattern: `patients/{patient_id}/reports/{report_id}/{filename}`

2. **IAM Conditions**: Add conditions to enforce patient-specific access
   ```json
   {
     "Condition": {
       "StringLike": {
         "s3:prefix": "patients/${aws:userid}/*"
       }
     }
   }
   ```

3. **Bucket Policy Conditions**: Restrict access based on patient ID
   ```json
   {
     "Condition": {
       "StringEquals": {
         "s3:x-amz-meta-patient-id": "${aws:userid}"
       }
     }
   }
   ```

## Monitoring and Alerts

### CloudWatch Metrics

Monitor the following S3 metrics:

- `BucketSizeBytes`
- `NumberOfObjects`
- `4xxErrors`
- `5xxErrors`
- `FirstByteLatency`
- `TotalRequestLatency`

### Recommended Alarms

1. **High Error Rate**: Alert when 4xx/5xx error rate exceeds 5%
2. **High Latency**: Alert when latency exceeds 1 second
3. **Unusual Access Patterns**: Alert on unusual access patterns
4. **Public Access Attempts**: Alert on denied public access attempts

## Compliance Considerations

### HIPAA Requirements

1. **Encryption at Rest**: All objects must be encrypted
2. **Encryption in Transit**: HTTPS only
3. **Access Controls**: Role-based access with audit logging
4. **Audit Trails**: Enable CloudTrail and S3 access logs
5. **Data Retention**: Implement appropriate retention policies
6. **Backup and Recovery**: Enable versioning and cross-region replication

### GDPR Considerations

1. **Data Minimization**: Store only necessary patient data
2. **Right to Erasure**: Implement deletion workflows
3. **Data Portability**: Support data export functionality
4. **Consent Management**: Track consent for data processing
5. **Breach Notification**: Implement breach detection and notification

## Implementation Checklist

- [ ] Create S3 buckets with appropriate naming
- [ ] Enable block public access
- [ ] Enable server-side encryption (SSE-KMS recommended)
- [ ] Enable bucket versioning
- [ ] Apply bucket policies
- [ ] Configure lifecycle rules
- [ ] Enable access logging
- [ ] Enable CloudTrail data events
- [ ] Create IAM roles with least privilege
- [ ] Configure CloudWatch alarms
- [ ] Test patient data isolation
- [ ] Verify encryption requirements
- [ ] Document backup and recovery procedures

## Post-Sprint 8 Implementation

These S3 bucket policies and configurations must be implemented manually after Sprint 8 completion. The infrastructure team should:

1. Review and customize the policies for the specific AWS account
2. Replace placeholder values (account-id, region) with actual values
3. Create the buckets with the recommended configurations
4. Apply the bucket policies
5. Enable all security features (encryption, versioning, logging)
6. Configure lifecycle rules for cost optimization
7. Set up CloudWatch alarms for monitoring
8. Test the configuration with sample data
9. Verify patient data isolation works correctly
10. Document any deviations from the recommended policies

## References

- [AWS S3 Bucket Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policies.html)
- [AWS S3 Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [HIPAA Compliance on AWS](https://aws.amazon.com/compliance/hipaa/)
- [GDPR on AWS](https://aws.amazon.com/compliance/gdpr/)
