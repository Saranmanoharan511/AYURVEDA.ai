# AWS Setup Guide for Ayurveda AI Platform
## Using AWS Nova Micro and Amazon Titan Text Embeddings V2

This guide provides step-by-step instructions for setting up the AWS resources required to run the Ayurveda AI Platform with AWS Nova Micro and Amazon Titan Text Embeddings V2.

---

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Neon PostgreSQL** account (for managed database)
4. **Domain name** (for production deployment)

---

## 1. AWS Services Overview

The platform requires the following AWS services:

| Service | Purpose | Cost Considerations |
|---------|---------|-------------------|
| **Amazon Bedrock** | LLM (Nova Micro) + Embeddings (Titan V2) | Pay-per-use, Nova Micro is cost-efficient |
| **Amazon S3** | Document storage | Pay for storage + requests |
| **Amazon SQS** | Async message queues | Pay per million requests |
| **Amazon Cognito** | User authentication | Free tier available |
| **Amazon SES** | Email notifications | Pay per email sent |
| **Amazon Textract** | Document OCR | Pay per page processed |
| **Amazon CloudWatch** | Logging & monitoring | Free tier + paid features |
| **AWS IAM** | Access management | Free |

---

## 2. AWS Bedrock Setup

### 2.1 Enable Amazon Bedrock Access

1. Go to **AWS Console** → **Amazon Bedrock**
2. Click **"Get started"** or navigate to **"Model access"**
3. Request access to the following models:
   - **AWS Nova Micro**: `us.amazon.nova-micro-v1:0`
   - **Amazon Titan Text Embeddings V2**: `amazon.titan-embed-text-v2:0`

### 2.2 Verify Model Access

```bash
# List available Bedrock models
aws bedrock list-foundation-models --region us-east-1

# Check specific model availability
aws bedrock get-foundation-model --model-id us.amazon.nova-micro-v1:0 --region us-east-1
aws bedrock get-foundation-model --model-id amazon.titan-embed-text-v2:0 --region us-east-1
```

### 2.3 Create Bedrock Guardrails (Optional but Recommended)

1. Go to **Amazon Bedrock** → **Guardrails**
2. Click **"Create guardrail"**
3. Configure:
   - **Name**: `Ayurveda-AI-Guardrail`
   - **Content filters**: HATE_SPEECH, INSULTS, SEXUAL, VIOLENCE
   - **Blocked words**: Add medical diagnosis terms
   - **Blocked topics**: Medical advice, prescription recommendations
4. Note the **Guardrail ID** and **Version** for your `.env` file

---

## 3. IAM Policy Setup

### 3.1 Create IAM Policy for Application

Create a policy file `ayurveda-ai-policy.json`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel"
            ],
            "Resource": [
                "arn:aws:bedrock:*:*:foundation-model/us.amazon.nova-micro-v1:0",
                "arn:aws:bedrock:*:*:foundation-model/amazon.titan-embed-text-v2:0"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:ApplyGuardrail",
                "bedrock:CreateGuardrail",
                "bedrock:GetGuardrail",
                "bedrock:UpdateGuardrail"
            ],
            "Resource": "arn:aws:bedrock:*:*:guardrail/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::ayurveda-ai-documents",
                "arn:aws:s3:::ayurveda-ai-documents/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "sqs:SendMessage",
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:ChangeMessageVisibility"
            ],
            "Resource": [
                "arn:aws:sqs:*:*:ayurveda-ai-document-queue",
                "arn:aws:sqs:*:*:ayurveda-ai-email-queue",
                "arn:aws:sqs:*:*:ayurveda-ai-dlq-documents",
                "arn:aws:sqs:*:*:ayurveda-ai-dlq-email"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "cognito-idp:AdminInitiateAuth",
                "cognito-idp:AdminRespondToAuthChallenge",
                "cognito-idp:AdminCreateUser",
                "cognito-idp:AdminDeleteUser",
                "cognito-idp:AdminGetUser",
                "cognito-idp:AdminUpdateUserAttributes"
            ],
            "Resource": "arn:aws:cognito-idp:*:*:userpool/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail",
                "ses:VerifyEmailIdentity"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "textract:DetectDocumentText",
                "textract:StartDocumentTextDetection",
                "textract:GetDocumentTextDetection"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            "Resource": "arn:aws:logs:*:*:log-group:/ayurveda-ai/*"
        }
    ]
}
```

### 3.2 Create IAM User and Attach Policy

```bash
# Create IAM user
aws iam create-user --user-name ayurveda-ai-app

# Attach policy
aws iam put-user-policy --user-name ayurveda-ai-app --policy-name AyurvedaAIPolicy --policy-document file://ayurveda-ai-policy.json

# Create access key
aws iam create-access-key --user-name ayurveda-ai-app
```

**Save the Access Key ID and Secret Access Key** for your `.env` file.

---

## 4. S3 Bucket Setup

### 4.1 Create S3 Bucket for Documents

```bash
# Create bucket (replace with your unique name)
aws s3api create-bucket \
    --bucket ayurveda-ai-documents-$(date +%s) \
    --region us-east-1 \
    --create-bucket-configuration LocationConstraint=us-east-1
```

### 4.2 Configure Bucket Policy

Create `s3-bucket-policy.json`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyUnencryptedObjectUploads",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*",
            "Condition": {
                "StringNotEquals": {
                    "s3:x-amz-server-side-encryption": "AES256"
                }
            }
        },
        {
            "Sid": "DenyInsecureConnections",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*",
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        }
    ]
}
```

Apply the policy:

```bash
aws s3api put-bucket-policy \
    --bucket YOUR-BUCKET-NAME \
    --policy file://s3-bucket-policy.json
```

### 4.3 Enable Versioning (Optional but Recommended)

```bash
aws s3api put-bucket-versioning \
    --bucket YOUR-BUCKET-NAME \
    --versioning-configuration Status=Enabled
```

---

## 5. SQS Queue Setup

### 5.1 Create Document Processing Queue

```bash
# Create main queue
aws sqs create-queue \
    --queue-name ayurveda-ai-document-queue \
    --region us-east-1

# Create DLQ for failed messages
aws sqs create-queue \
    --queue-name ayurveda-ai-dlq-documents \
    --region us-east-1

# Configure redrive policy
aws sqs set-queue-attributes \
    --queue-url https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT-ID/ayurveda-ai-document-queue \
    --attributes '{
        "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:YOUR-ACCOUNT-ID:ayurveda-ai-dlq-documents\",\"maxReceiveCount\":\"3\"}"
    }'
```

### 5.2 Create Email Queue

```bash
# Create email queue
aws sqs create-queue \
    --queue-name ayurveda-ai-email-queue \
    --region us-east-1

# Create DLQ for email
aws sqs create-queue \
    --queue-name ayurveda-ai-dlq-email \
    --region us-east-1

# Configure redrive policy
aws sqs set-queue-attributes \
    --queue-url https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT-ID/ayurveda-ai-email-queue \
    --attributes '{
        "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:YOUR-ACCOUNT-ID:ayurveda-ai-dlq-email\",\"maxReceiveCount\":\"3\"}"
    }'
```

**Save the Queue URLs** for your `.env` file.

---

## 6. Amazon Cognito Setup

### 6.1 Create User Pool

```bash
aws cognito-idp create-user-pool \
    --pool-name Ayurveda-AI-User-Pool \
    --policies '{
        "PasswordPolicy": {
            "MinimumLength": 8,
            "RequireUppercase": true,
            "RequireLowercase": true,
            "RequireNumbers": true,
            "RequireSymbols": false
        }
    }' \
    --auto-verified-attributes email \
    --username-attributes email \
    --region us-east-1
```

### 6.2 Create App Client

```bash
aws cognito-idp create-user-pool-client \
    --user-pool-id YOUR-USER-POOL-ID \
    --client-name Ayurveda-AI-Web-Client \
    --no-generate-secret \
    --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
    --region us-east-1
```

### 6.3 Create User Groups

```bash
# Create Doctor group
aws cognito-idp create-group \
    --user-pool-id YOUR-USER-POOL-ID \
    --group-name Doctors \
    --description "Doctor users"

# Create Patient group
aws cognito-idp create-group \
    --user-pool-id YOUR-USER-POOL-ID \
    --group-name Patients \
    --description "Patient users"

# Create Admin group
aws cognito-idp create-group \
    --user-pool-id YOUR-USER-POOL-ID \
    --group-name Admins \
    --description "Admin users"
```

**Save the User Pool ID and Client ID** for your `.env` file.

---

## 7. Amazon SES Setup

### 7.1 Verify Email Identity

```bash
# Verify your email domain
aws ses verify-email-identity \
    --email your-domain@example.com \
    --region us-east-1

# Or verify individual email
aws ses verify-email-identity \
    --email noreply@yourdomain.com \
    --region us-east-1
```

### 7.2 Move Out of Sandbox (Production Only)

For production, you need to request to move out of the SES sandbox:

1. Go to **Amazon SES** → **Sending Statistics**
2. Click **"Request production access"**
3. Fill out the form with your use case details

**Save the verified email** for your `.env` file.

---

## 8. Amazon Textract Setup

### 8.1 Enable Textract Access

Textract is available in most regions by default. Verify access:

```bash
# Test Textract access
aws textract detect-document-text \
    --document '{"S3Object":{"Bucket":"your-bucket","Name":"test.pdf"}}' \
    --region us-east-1
```

### 8.2 Configure S3 Access for Textract

Ensure your IAM policy includes Textract permissions (already included in the policy above).

---

## 9. CloudWatch Setup

### 9.1 Create Log Groups

```bash
# Create backend log group
aws logs create-log-group \
    --log-group-name /ayurveda-ai/backend \
    --region us-east-1

# Create production log group
aws logs create-log-group \
    --log-group-name /ayurveda-ai/backend-production \
    --region us-east-1
```

### 9.2 Create CloudWatch Alarms (Optional)

```bash
# Create error rate alarm
aws cloudwatch put-metric-alarm \
    --alarm-name ayurveda-ai-high-error-rate \
    --alarm-description "Alert when error rate exceeds threshold" \
    --metric-name Errors \
    --namespace Ayurveda-AI \
    --statistic Sum \
    --period 60 \
    --evaluation-periods 1 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --region us-east-1
```

---

## 10. Environment Configuration

### 10.1 Update Your `.env` File

Copy `.env.example` to `.env` and fill in the values:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY

# S3 Configuration
S3_BUCKET_NAME=your-s3-bucket-name

# SQS Configuration
SQS_DOCUMENT_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT-ID/ayurveda-ai-document-queue
SQS_EMAIL_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT-ID/ayurveda-ai-email-queue
DLQ_DOCUMENT_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT-ID/ayurveda-ai-dlq-documents
DLQ_EMAIL_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT-ID/ayurveda-ai-dlq-email

# Cognito Configuration
COGNITO_USER_POOL_ID=your-user-pool-id
COGNITO_CLIENT_ID=your-client-id
COGNITO_REGION=us-east-1

# Bedrock Configuration
BEDROCK_MODEL_ID=us.amazon.nova-micro-v1:0
BEDROCK_GUARDRAIL_ID=your-guardrail-id  # Optional
BEDROCK_GUARDRAIL_VERSION=DRAFT

# SES Configuration
SES_FROM_EMAIL=noreply@yourdomain.com
SES_REGION=us-east-1

# Embedding Configuration
EMBEDDING_PROVIDER=bedrock
EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
EMBEDDING_DIMENSIONS=1024

# Database - Neon PostgreSQL
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require

# Other configuration...
SECRET_KEY=your-secret-key-change-in-production
```

---

## 11. Neon PostgreSQL Setup

### 11.1 Create Neon Project

1. Go to [Neon Console](https://console.neon.tech/)
2. Click **"Create a project"**
3. Choose region (preferably same as AWS region)
4. Copy the connection string

### 11.2 Enable pgvector Extension

```sql
-- Connect to your Neon database
CREATE EXTENSION IF NOT EXISTS vector;
```

### 11.3 Run Database Migrations

```bash
cd backend
alembic upgrade head
```

**Note**: The migrations have been updated to use 1024-dimensional vectors (matching Titan V2). If you have an existing database with 1536-dimensional vectors, migration 017 will update the schema to 1024 dimensions, but existing embeddings will need to be regenerated.

### 11.3 Run Database Migrations

```bash
cd backend
alembic upgrade head
```

---

## 12. Testing the Configuration

### 12.1 Test Bedrock Access

```bash
cd backend
python -c "
from app.services.bedrock_service import BedrockService
service = BedrockService()
print('Bedrock available:', service.is_available())
print('Available models:', service.list_available_models())
"
```

### 12.2 Test Embedding Service

```bash
python -c "
from app.services.embedding_service import embedding_service
embedding = embedding_service.generate_embedding('test text')
print('Embedding generated:', len(embedding) if embedding else 'Failed')
"
```

### 12.3 Test Textract Access

```bash
python -c "
from app.services.textract_service import textract_service
print('Textract configured: True')
"
```

---

## 13. Cost Optimization Tips

### 13.1 AWS Nova Micro Cost Advantages

- **Text-only model**: Lowest cost in Nova family
- **Fast inference**: Reduces compute time
- **Efficient for**: Summarization, Q&A, classification

### 13.2 Titan Embeddings V2 Cost Advantages

- **Improved quality**: Better embeddings with similar cost
- **1024 dimensions**: Smaller vectors = lower storage costs
- **Batch processing**: Process multiple texts efficiently

### 13.3 General Cost Optimization

1. **Use S3 Intelligent Tiering** for document storage
2. **Set SQS message retention** appropriately (default 4 days)
3. **Monitor CloudWatch metrics** to avoid over-provisioning
4. **Use Cognito free tier** (50,000 MAUs/month)
5. **Implement caching** for frequently accessed data

---

## 14. Security Best Practices

### 14.1 IAM Security

- Use **least privilege** principle
- Rotate access keys regularly
- Use **IAM roles** instead of access keys in production
- Enable **MFA** for root account

### 14.2 Data Security

- Enable **S3 server-side encryption**
- Use **HTTPS only** for all communications
- Implement **VPC endpoints** for AWS services
- Regular **security audits**

### 14.3 Application Security

- Never commit `.env` files
- Use **environment-specific** configurations
- Implement **rate limiting** (already configured)
- Enable **audit logging** (already configured)

---

## 15. Troubleshooting

### 15.1 Bedrock Access Denied

```bash
# Check model access
aws bedrock list-foundation-models --region us-east-1

# Request model access in AWS Console
```

### 15.2 S3 Access Issues

```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket YOUR-BUCKET-NAME

# Check IAM permissions
aws iam get-user-policy --user-name ayurveda-ai-app --policy-name AyurvedaAIPolicy
```

### 15.3 SQS Queue Not Receiving Messages

```bash
# Check queue attributes
aws sqs get-queue-attributes \
    --queue-url YOUR-QUEUE-URL \
    --attribute-names All

# Check IAM permissions for SQS
```

### 15.4 Neon PostgreSQL Connection Issues

```bash
# Test connection
psql "postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require"

# Check pgvector extension
psql -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

---

## 16. Production Deployment Checklist

- [ ] All AWS resources created and configured
- [ ] IAM policies with least privilege
- [ ] S3 bucket policies configured
- [ ] SQS queues with DLQ configured
- [ ] Cognito user pool with groups
- [ ] SES email verified (or sandbox access)
- [ ] Bedrock model access enabled
- [ ] Textract access verified
- [ ] CloudWatch log groups created
- [ ] Neon PostgreSQL with pgvector enabled
- [ ] Database migrations run
- [ ] Environment variables configured
- [ ] SSL/TLS enabled everywhere
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery plan documented
- [ ] Security audit completed

---

## 17. Estimated Monthly Costs (US-East-1)

| Service | Usage | Estimated Cost |
|---------|-------|----------------|
| **Bedrock Nova Micro** | 100K tokens/day | ~$30-50/month |
| **Titan Embeddings V2** | 10K embeddings/day | ~$5-10/month |
| **S3 Storage** | 100 GB documents | ~$2.30/month |
| **SQS** | 10K requests/day | ~$0.10/month |
| **Cognito** | 1K MAUs | Free tier |
| **SES** | 1K emails/month | ~$0.10/month |
| **Textract** | 100 pages/day | ~$1.50/month |
| **CloudWatch** | Basic logging | ~$5-10/month |
| **Neon PostgreSQL** | Basic tier | ~$19-25/month |
| **Total** | | **~$63-107/month** |

*Note: These are rough estimates. Actual costs depend on usage patterns.*

---

## 18. Support and Resources

- **AWS Documentation**: https://docs.aws.amazon.com/
- **Bedrock Documentation**: https://docs.aws.amazon.com/bedrock/
- **Neon Documentation**: https://neon.tech/docs
- **Project Issues**: GitHub repository issues

---

## Summary

This setup configures your Ayurveda AI Platform to use:
- **AWS Nova Micro** (`us.amazon.nova-micro-v1:0`) for cost-efficient LLM operations
- **Amazon Titan Text Embeddings V2** (`amazon.titan-embed-text-v2:0`) for high-quality embeddings
- All necessary AWS services for document processing, authentication, and notifications

The configuration changes ensure your application uses these specific models while maintaining all existing functionality for patient data isolation, security, and HIPAA compliance considerations.
