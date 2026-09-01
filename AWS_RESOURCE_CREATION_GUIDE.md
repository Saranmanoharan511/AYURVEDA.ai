# AWS Resource Creation Guide (Post-Sprint 8)

## Overview

This document provides step-by-step instructions for creating all required AWS resources for the Ayurveda-AI platform. These procedures are to be executed after Sprint 8 when infrastructure deployment begins.

**Important:** This guide is for post-Sprint 8 infrastructure integration. Do not execute these steps during Sprint 8.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [S3 Bucket Creation](#s3-bucket-creation)
3. [SQS Queue Creation](#sqs-queue-creation)
4. [Cognito User Pool Creation](#cognito-user-pool-creation)
5. [SES Configuration](#ses-configuration)
6. [Bedrock Configuration](#bedrock-configuration)
7. [CloudWatch Configuration](#cloudwatch-configuration)
8. [IAM Role Creation](#iam-role-creation)
9. [Lightsail Instance Setup](#lightsail-instance-setup)
10. [Security Group Configuration](#security-group-configuration)

---

## Prerequisites

### AWS Account Setup

- AWS account with appropriate permissions
- AWS CLI installed and configured
- AWS region selected (recommended: us-east-1)
- Billing alerts configured

### Required Permissions

The following IAM permissions are required:
- s3:*
- sqs:*
- cognito-idp:*
- ses:*
- bedrock:*
- cloudwatch:*
- iam:*
- lightsail:*
- ec2:*

### Naming Convention

Use consistent naming convention:
- Prefix: `ayurveda-ai`
- Environment suffix: `-dev`, `-staging`, `-prod`
- Example: `ayurveda-ai-documents-prod`

---

## S3 Bucket Creation

### Document Storage Bucket

#### 1. Create Bucket

```bash
aws s3api create-bucket \
  --bucket ayurveda-ai-documents-prod \
  --region us-east-1 \
  --create-bucket-configuration LocationConstraint=us-east-1
```

#### 2. Enable Versioning

```bash
aws s3api put-bucket-versioning \
  --bucket ayurveda-ai-documents-prod \
  --versioning-configuration Status=Enabled
```

#### 3. Enable Server-Side Encryption

```bash
aws s3api put-bucket-encryption \
  --bucket ayurveda-ai-documents-prod \
  --server-side-encryption-configuration \
  '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }
    ]
  }'
```

#### 4. Configure Bucket Policy

Create `bucket-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAppAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<account-id>:role/ayurveda-backend-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::ayurveda-ai-documents-prod/*"
    },
    {
      "Sid": "DenyPublicAccess",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::ayurveda-ai-documents-prod",
        "arn:aws:s3:::ayurveda-ai-documents-prod/*"
      ]
    }
  ]
}
```

Apply policy:

```bash
aws s3api put-bucket-policy \
  --bucket ayurveda-ai-documents-prod \
  --policy file://bucket-policy.json
```

#### 5. Enable Public Access Block

```bash
aws s3api put-public-access-block \
  --bucket ayurveda-ai-documents-prod \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

#### 6. Configure Lifecycle Rule (Optional)

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket ayurveda-ai-documents-prod \
  --lifecycle-configuration \
  '{
    "Rules": [
      {
        "Id": "DeleteOldVersions",
        "Status": "Enabled",
        "NoncurrentVersionExpiration": {
          "NoncurrentVersionDays": 30
        }
      }
    ]
  }'
```

---

## SQS Queue Creation

### Document Processing Queue

#### 1. Create Queue

```bash
aws sqs create-queue \
  --queue-name ayurveda-ai-document-queue-prod \
  --region us-east-1 \
  --attributes \
    DelaySeconds=0, \
    MaximumMessageSize=262144, \
    MessageRetentionPeriod=1209600, \
    ReceiveMessageWaitTimeSeconds=20, \
    VisibilityTimeout=300
```

#### 2. Create Dead Letter Queue

```bash
aws sqs create-queue \
  --queue-name ayurveda-ai-document-dlq-prod \
  --region us-east-1
```

#### 3. Configure Redrive Policy

```bash
aws sqs set-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/<account-id>/ayurveda-ai-document-queue-prod \
  --attributes \
    '{
      "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:<account-id>:ayurveda-ai-document-dlq-prod\",\"maxReceiveCount\":\"3\"}"
    }'
```

### Email Queue

Repeat steps for email queue:

```bash
aws sqs create-queue \
  --queue-name ayurveda-ai-email-queue-prod \
  --region us-east-1

aws sqs create-queue \
  --queue-name ayurveda-ai-email-dlq-prod \
  --region us-east-1
```

---

## Cognito User Pool Creation

#### 1. Create User Pool

```bash
aws cognito-idp create-user-pool \
  --pool-name ayurveda-ai-user-pool-prod \
  --policies \
    '{
      "PasswordPolicy": {
        "MinimumLength": 8,
        "RequireUppercase": true,
        "RequireLowercase": true,
        "RequireNumbers": true,
        "RequireSymbols": true
      }
    }' \
  --auto-verified-attributes email \
  --username-attributes email \
  --alias-attributes email \
  --mfa-configuration OPTIONAL
```

Save the User Pool ID from the response.

#### 2. Create User Pool Client

```bash
aws cognito-idp create-user-pool-client \
  --user-pool-id <user-pool-id> \
  --client-name ayurveda-ai-web-client \
  --generate-secret \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH,ALLOW_REFRESH_TOKEN_AUTH \
  --allowed-o-auth-flows code \
  --allowed-o-auth-scopes email,openid,profile \
  --callback-urls https://yourdomain.com \
  --logout-urls https://yourdomain.com
```

Save the Client ID and Client Secret from the response.

#### 3. Create User Pool Domain

```bash
aws cognito-idp create-user-pool-domain \
  --domain ayurveda-ai-prod \
  --user-pool-id <user-pool-id>
```

#### 4. Create Groups

```bash
# Patient Group
aws cognito-idp create-group \
  --user-pool-id <user-pool-id> \
  --group-name patients \
  --description "Patient users"

# Doctor Group
aws cognito-idp create-group \
  --user-pool-id <user-pool-id> \
  --group-name doctors \
  --description "Doctor users"

# Admin Group
aws cognito-idp create-group \
  --user-pool-id <user-pool-id> \
  --group-name admins \
  --description "Admin users"
```

#### 5. Configure Lambda Triggers (Optional)

Configure triggers for:
- Pre-signup
- Post-confirmation
- Pre-token-generation
- Post-authentication

---

## SES Configuration

#### 1. Verify Email Domain

```bash
aws ses verify-email-identity \
  --email-domain yourdomain.com
```

#### 2. Verify Email Address (for testing)

```bash
aws ses verify-email-identity \
  --email-address noreply@yourdomain.com
```

#### 3. Create Email Template

Create `welcome-template.json`:

```json
{
  "TemplateName": "WelcomeTemplate",
  "SubjectPart": "Welcome to Ayurveda AI Platform",
  "HtmlPart": "<h1>Welcome {{name}}</h1><p>Thank you for registering with Ayurveda AI Platform.</p>",
  "TextPart": "Welcome {{name}}. Thank you for registering with Ayurveda AI Platform."
}
```

Apply template:

```bash
aws ses create-template \
  --cli-input-json file://welcome-template.json
```

#### 4. Create Additional Templates

Create templates for:
- Consultation confirmation
- Appointment reminder
- Report delivery
- Password reset

#### 5. Configure Sending Limits

Request production access if needed:
- Navigate to SES console
- Request sending limit increase
- Provide use case details

---

## Bedrock Configuration

#### 1. Enable Bedrock Access

```bash
# Navigate to AWS Console > Bedrock
# Request access to required models
# Models needed:
# - anthropic.claude-3-sonnet-20240229-v1:0
# - amazon.titan-embed-text-v1 (for embeddings)
```

#### 2. Create Guardrail

```bash
aws bedrock create-guardrail \
  --name ayurveda-ai-guardrail \
  --description "Guardrails for medical AI assistant" \
  --blocked-inputs \
    '{
      "blockedPhrases": [
        {"phrase": "ignore previous instructions"},
        {"phrase": "override system prompt"},
        {"phrase": "act as admin"}
      ]
    }' \
  --blocked-outputs \
    '{
      "blockedPhrases": [
        {"phrase": "I diagnose"},
        {"phrase": "I prescribe"},
        {"phrase": "you must take"}
      ]
    }' \
  --content-blocking-config \
    '{
      "filtersConfig": [
        {
          "type": "SEXUAL",
          "inputStrength": "HIGH",
          "outputStrength": "HIGH"
        },
        {
          "type": "VIOLENCE",
          "inputStrength": "HIGH",
          "outputStrength": "HIGH"
        },
        {
          "type": "HATE",
          "inputStrength": "HIGH",
          "outputStrength": "HIGH"
        }
      ]
    }'
```

Save the Guardrail ID from the response.

#### 3. Create Guardrail Version

```bash
aws bedrock create-guardrail-version \
  --guardrail-identifier <guardrail-id> \
  --description "Initial version"
```

#### 4. Test Bedrock Access

```bash
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body '{"inputText": "Hello"}' \
  --cli-binary-format raw-in-base64-out
```

---

## CloudWatch Configuration

#### 1. Create Log Groups

```bash
# Backend logs
aws logs create-log-group \
  --log-group-name /ayurveda-ai/backend-prod \
  --retention-in-days 30

# Worker logs
aws logs create-log-group \
  --log-group-name /ayurveda-ai/workers-prod \
  --retention-in-days 30

# Application logs
aws logs create-log-group \
  --log-group-name /ayurveda-ai/application-prod \
  --retention-in-days 30
```

#### 2. Create Metric Filters

```bash
# Error metric filter
aws logs put-metric-filter \
  --log-group-name /ayurveda-ai/backend-prod \
  --filter-name error-filter \
  --filter-pattern "[timestamp, request_id, level=ERROR, ...]" \
  --metric-transformations \
    metricName=ErrorCount,metricNamespace=AyurvedaAI,metricValue=1
```

#### 3. Create Alarms

Create `error-alarm.json`:

```json
{
  "AlarmName": "ayurveda-ai-error-alarm",
  "AlarmDescription": "Alert when error rate exceeds threshold",
  "MetricName": "ErrorCount",
  "Namespace": "AyurvedaAI",
  "Statistic": "Sum",
  "Period": 60,
  "EvaluationPeriods": 5,
  "Threshold": 5,
  "ComparisonOperator": "GreaterThanThreshold",
  "TreatMissingData": "notBreaching"
}
```

Apply alarm:

```bash
aws cloudwatch put-metric-alarm \
  --cli-input-json file://error-alarm.json
```

#### 4. Create SNS Topic for Alerts

```bash
aws sns create-topic \
  --name ayurveda-ai-alerts-prod
```

#### 5. Subscribe to SNS Topic

```bash
aws sns subscribe \
  --topic-arn <sns-topic-arn> \
  --protocol email \
  --notification-endpoint admin@yourdomain.com
```

#### 6. Link Alarm to SNS Topic

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name ayurveda-ai-error-alarm \
  --alarm-actions <sns-topic-arn>
```

---

## IAM Role Creation

#### 1. Create Backend IAM Role

Create `backend-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lightsail.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Create role:

```bash
aws iam create-role \
  --role-name ayurveda-backend-role \
  --assume-role-policy-document file://backend-trust-policy.json
```

#### 2. Attach Policies to Backend Role

Create `backend-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::ayurveda-ai-documents-prod/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": [
        "arn:aws:sqs:us-east-1:<account-id>:ayurveda-ai-document-queue-prod",
        "arn:aws:sqs:us-east-1:<account-id>:ayurveda-ai-email-queue-prod"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:ApplyGuardrail",
        "bedrock:CreateGuardrailVersion"
      ],
      "Resource": "arn:aws:bedrock:us-east-1:<account-id>:guardrail/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:<account-id>:log-group:/ayurveda-ai/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:AdminInitiateAuth",
        "cognito-idp:AdminCreateUser",
        "cognito-idp:AdminDeleteUser",
        "cognito-idp:AdminGetUser",
        "cognito-idp:AdminUpdateUserAttributes",
        "cognito-idp:ListUsers"
      ],
      "Resource": "arn:aws:cognito-idp:us-east-1:<account-id>:userpool/*"
    }
  ]
}
```

Create policy:

```bash
aws iam create-policy \
  --policy-name ayurveda-backend-policy \
  --policy-document file://backend-policy.json
```

Attach policy:

```bash
aws iam attach-role-policy \
  --role-name ayurveda-backend-role \
  --policy-arn arn:aws:iam::<account-id>:policy/ayurveda-backend-policy
```

#### 3. Create Worker IAM Role

Similar to backend role but with SQS permissions only.

---

## Lightsail Instance Setup

#### 1. Create Lightsail Instance

```bash
aws lightsail create-instances \
  --instance-names ayurveda-backend-prod \
  --availability-zone us-east-1a \
  --blueprint-id ubuntu_22_04 \
  --bundle-id medium_2_0 \
  --user-data file://user-data.sh
```

Create `user-data.sh`:

```bash
#!/bin/bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create app directory
mkdir -p /opt/ayurveda-ai
cd /opt/ayurveda-ai

# Create .env file
touch .env.production
```

#### 2. Configure Static IP

```bash
aws lightsail allocate-static-ip \
  --region us-east-1
```

Attach to instance:

```bash
aws lightsail attach-static-ip \
  --instance-name ayurveda-backend-prod \
  --static-ip-name <static-ip-name>
```

#### 3. Configure DNS

Add A record in your DNS provider:
- Name: api
- Value: <static-ip>

#### 4. Configure SSL with Let's Encrypt

```bash
# SSH into instance
ssh ubuntu@<static-ip>

# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal is configured automatically
```

---

## Security Group Configuration

#### 1. Create Security Group

```bash
aws ec2 create-security-group \
  --group-name ayurveda-backend-sg \
  --description "Security group for Ayurveda AI backend" \
  --vpc-id <vpc-id>
```

#### 2. Add Inbound Rules

```bash
# Allow HTTP
aws ec2 authorize-security-group-ingress \
  --group-id <security-group-id> \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow HTTPS
aws ec2 authorize-security-group-ingress \
  --group-id <security-group-id> \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Allow SSH (restrict to specific IP)
aws ec2 authorize-security-group-ingress \
  --group-id <security-group-id> \
  --protocol tcp \
  --port 22 \
  --cidr <your-ip>/32
```

#### 3. Attach Security Group to Lightsail Instance

```bash
aws lightsail open-instance-public-ports \
  --instance-name ayurveda-backend-prod \
  --port-info fromPort=80,toPort=80,protocol=TCP

aws lightsail open-instance-public-ports \
  --instance-name ayurveda-backend-prod \
  --port-info fromPort=443,toPort=443,protocol=TCP
```

---

## Verification Steps

### 1. Verify S3 Bucket

```bash
aws s3 ls s3://ayurveda-ai-documents-prod
```

### 2. Verify SQS Queues

```bash
aws sqs list-queues
```

### 3. Verify Cognito User Pool

```bash
aws cognito-idp describe-user-pool \
  --user-pool-id <user-pool-id>
```

### 4. Verify SES

```bash
aws ses get-account-sending-enabled
```

### 5. Verify Bedrock

```bash
aws bedrock list-foundation-models
```

### 6. Verify CloudWatch

```bash
aws logs describe-log-groups \
  --log-group-name-prefix /ayurveda-ai
```

### 7. Verify IAM Roles

```bash
aws iam list-roles
```

### 8. Verify Lightsail Instance

```bash
aws lightsail get-instances \
  --instance-names ayurveda-backend-prod
```

---

## Cleanup Commands

If you need to delete resources:

```bash
# Delete S3 bucket (must empty first)
aws s3 rm s3://ayurveda-ai-documents-prod --recursive
aws s3api delete-bucket --bucket ayurveda-ai-documents-prod

# Delete SQS queues
aws sqs delete-queue --queue-url <queue-url>

# Delete Cognito User Pool
aws cognito-idp delete-user-pool --user-pool-id <user-pool-id>

# Delete IAM roles
aws iam delete-role --role-name ayurveda-backend-role

# Delete Lightsail instance
aws lightsail delete-instance --instance-name ayurveda-backend-prod
```

---

## Appendix

### Cost Estimates

- S3: ~$0.023/GB/month
- SQS: ~$0.40 per million requests
- Cognito: ~$0.0055 per MAU
- SES: $0.10 per 1000 emails (first 62,000/month free)
- Bedrock: Varies by model usage
- CloudWatch Logs: ~$0.50/GB per month
- Lightsail: ~$20/month (medium instance)

### Monitoring

Set up billing alerts:
- Navigate to AWS Billing Console
- Create budget
- Set alert thresholds

### Security Best Practices

- Use IAM roles instead of access keys where possible
- Enable MFA for root account
- Rotate credentials regularly
- Enable AWS Config
- Enable CloudTrail
- Use VPC endpoints where applicable

---

**Note:** This AWS resource creation guide should be updated as infrastructure requirements evolve.
