# CI/CD Deployment Guide (Post-Sprint 8)

## Overview

This document provides step-by-step instructions for setting up CI/CD pipelines for the Ayurveda-AI platform. These procedures are to be executed after Sprint 8 when infrastructure (AWS, Neon) has been deployed.

**Important:** This guide is for post-Sprint 8 infrastructure integration. Do not execute these steps during Sprint 8.

---

## Table of Contents

1. [Frontend CI/CD (AWS Amplify)](#frontend-cicd-aws-amplify)
2. [Backend CI/CD (GitHub Actions + AWS Lightsail)](#backend-cicd-github-actions--aws-lightsail)
3. [Database Migrations CI/CD](#database-migrations-cicd)
4. [Workers CI/CD](#workers-cicd)
5. [Environment Management](#environment-management)

---

## Frontend CI/CD (AWS Amplify)

### Prerequisites

- AWS Amplify CLI installed
- GitHub repository connected to Amplify
- Amplify app created
- Build settings configured

### Setup Steps

#### 1. Initialize Amplify

```bash
cd frontend
amplify init
```

Follow the prompts:
- Select environment: dev, staging, prod
- Select editor: VS Code
- Choose app type: JavaScript
- Choose framework: React
- Choose build directory: dist
- Choose distribution directory: dist

#### 2. Add Hosting

```bash
amplify add hosting
```

Select:
- Type: Single-page app (SPA)
- Custom domain: (optional)

#### 3. Configure Build Settings

Create `amplify.yml` in frontend root:

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: dist
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

#### 4. Connect to GitHub

```bash
amplify add hosting
```

Select:
- Plugin: Amplify Console
- Select: Continuous deployment (Git-based)
- Repository: Select your GitHub repository
- Branch: main

#### 5. Configure Environment Variables

In Amplify Console:
- Navigate to App Settings > Environment Variables
- Add variables:
  - `VITE_API_BASE_URL`: https://api.yourdomain.com
  - `VITE_API_VERSION`: v1
  - `VITE_ENVIRONMENT`: production
  - `VITE_COGNITO_USER_POOL_ID`: <your-pool-id>
  - `VITE_COGNITO_CLIENT_ID`: <your-client-id>

#### 6. Deploy

```bash
amplify publish
```

Or push to GitHub to trigger automatic deployment.

#### 7. Configure Custom Domain (Optional)

```bash
amplify add hosting
```

Select:
- Custom domain: Yes
- Domain: yourdomain.com
- Subdomain: www

---

## Backend CI/CD (GitHub Actions + AWS Lightsail)

### Prerequisites

- GitHub repository
- AWS Lightsail instance provisioned
- Docker registry (Docker Hub or AWS ECR)
- GitHub Actions enabled
- AWS credentials configured in GitHub Secrets

### Setup Steps

#### 1. Create GitHub Secrets

Navigate to GitHub repository > Settings > Secrets and variables > Actions

Add the following secrets:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
DOCKER_USERNAME
DOCKER_PASSWORD
DOCKER_REGISTRY
LIGHTSAIL_IP
SSH_PRIVATE_KEY
```

#### 2. Create GitHub Actions Workflow

Create `.github/workflows/backend-deploy.yml`:

```yaml
name: Backend Deploy

on:
  push:
    branches:
      - main
      - staging
  pull_request:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ secrets.DOCKER_REGISTRY }}
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: |
            ${{ secrets.DOCKER_REGISTRY }}/ayurveda-backend:latest
            ${{ secrets.DOCKER_REGISTRY }}/ayurveda-backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/staging'
    steps:
      - name: Deploy to Staging
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.LIGHTSAIL_IP_STAGING }}
          username: ubuntu
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            docker pull ${{ secrets.DOCKER_REGISTRY }}/ayurveda-backend:${{ github.sha }}
            docker stop ayurveda-backend
            docker rm ayurveda-backend
            docker run -d \
              --name ayurveda-backend \
              --env-file .env.staging \
              -p 8000:8000 \
              ${{ secrets.DOCKER_REGISTRY }}/ayurveda-backend:${{ github.sha }}

  deploy-production:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to Production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.LIGHTSAIL_IP }}
          username: ubuntu
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            docker pull ${{ secrets.DOCKER_REGISTRY }}/ ayurveda-backend:${{ github.sha }}
            docker stop ayurveda-backend
            docker rm ayurveda-backend
            docker run -d \
              --name ayurveda-backend \
              --env-file .env.production \
              -p 8000:8000 \
              ${{ secrets.DOCKER_REGISTRY }}/ayurveda-backend:${{ github.sha }}
      
      - name: Health Check
        run: |
          sleep 30
          curl -f https://api.yourdomain.com/api/v1/health || exit 1
```

#### 3. Configure Lightsail for SSH Access

On Lightsail instance:

```bash
# Create .ssh directory
mkdir -p ~/.ssh

# Add SSH key from GitHub
echo "${GITHUB_SSH_PUBLIC_KEY}" >> ~/.ssh/authorized_keys

# Set permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

#### 4. Configure Environment Files

On Lightsail instance:

```bash
# Create .env.staging
cp .env.example .env.staging
# Fill in staging values

# Create .env.production
cp .env.production.example .env.production
# Fill in production values
```

#### 5. Test Deployment

Push to staging branch:

```bash
git checkout staging
git push origin staging
```

Monitor GitHub Actions for deployment status.

---

## Database Migrations CI/CD

### Prerequisites

- Neon database provisioned
- Alembic configured
- Database connection string available

### Setup Steps

#### 1. Create Migration Workflow

Create `.github/workflows/database-migrate.yml`:

```yaml
name: Database Migration

on:
  push:
    branches:
      - main
    paths:
      - 'backend/alembic/versions/**'

jobs:
  migrate-staging:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/staging'
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run migrations
        env:
          DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
        run: |
          cd backend
          alembic upgrade head

  migrate-production:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Backup database
        run: |
          # Add backup command here
          echo "Backing up database..."
      
      - name: Run migrations
        env:
          DATABASE_URL: ${{ secrets.PRODUCTION_DATABASE_URL }}
        run: |
          cd backend
          alembic upgrade head
      
      - name: Verify migration
        run: |
          cd backend
          alembic current
```

#### 2. Add Database URLs to Secrets

Add to GitHub Secrets:
- `STAGING_DATABASE_URL`
- `PRODUCTION_DATABASE_URL`

---

## Workers CI/CD

### Prerequisites

- Worker Dockerfiles created
- Worker repositories configured
- SQS queues provisioned

### Setup Steps

#### 1. Create Document Processor Workflow

Create `.github/workflows/document-worker-deploy.yml`:

```yaml
name: Document Worker Deploy

on:
  push:
    branches:
      - main
    paths:
      - 'backend/workers/document_processor/**'

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ secrets.DOCKER_REGISTRY }}
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: ./backend/workers/document_processor
          push: true
          tags: |
            ${{ secrets.DOCKER_REGISTRY }}/document-worker:latest
            ${{ secrets.DOCKER_REGISTRY }}/document-worker:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Deploy Worker
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.LIGHTSAIL_IP }}
          username: ubuntu
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            docker pull ${{ secrets.DOCKER_REGISTRY }}/document-worker:${{ github.sha }}
            docker stop document-worker
            docker rm document-worker
            docker run -d \
              --name document-worker \
              --env-file .env.production \
              ${{ secrets.DOCKER_REGISTRY }}/document-worker:${{ github.sha }}
```

#### 2. Create Email Worker Workflow

Similar to document processor, but for email worker.

---

## Environment Management

### Branch Strategy

- `main`: Production branch
- `staging`: Staging branch
- `feature/*`: Feature branches

### Deployment Strategy

1. **Feature Development**
   - Create feature branch from main
   - Develop and test locally
   - Push to feature branch
   - Create pull request to staging

2. **Staging Deployment**
   - Merge to staging branch
   - Automatic deployment to staging
   - Test on staging environment
   - Fix any issues

3. **Production Deployment**
   - Create pull request from staging to main
   - Review and approve
   - Merge to main
   - Automatic deployment to production
   - Monitor production

### Rollback Procedure

If deployment fails:

1. **Identify Failed Deployment**
   - Check GitHub Actions logs
   - Identify commit that caused failure

2. **Revert Commit**
   ```bash
   git revert <commit-hash>
   git push origin main
   ```

3. **Deploy Previous Version**
   - Revert will trigger automatic deployment
   - Monitor deployment

4. **Verify Rollback**
   - Run health checks
   - Test critical functionality

---

## Monitoring CI/CD

### GitHub Actions Monitoring

- Monitor workflow runs in GitHub Actions tab
- Check for failed runs
- Review logs for errors
- Set up notifications for failures

### Deployment Notifications

Configure notifications:
- Slack integration for deployment alerts
- Email notifications for failures
- SMS alerts for critical failures

### Metrics to Track

- Deployment frequency
- Deployment success rate
- Deployment duration
- Rollback frequency
- Test pass rate

---

## Security Best Practices

### Secrets Management

- Never commit secrets to repository
- Use GitHub Secrets for sensitive data
- Rotate secrets regularly
- Use different secrets for different environments

### Access Control

- Restrict who can trigger deployments
- Require approval for production deployments
- Use branch protection rules
- Enable required status checks

### Security Scanning

- Add dependency scanning
- Add container scanning
- Add code scanning (CodeQL)
- Review security alerts regularly

---

## Troubleshooting

### Common Issues

#### Deployment Fails

**Symptoms**: GitHub Actions workflow fails

**Solutions**:
- Check workflow logs
- Verify secrets are configured
- Check Docker registry access
- Verify SSH access to Lightsail

#### Health Check Fails

**Symptoms**: Health check fails after deployment

**Solutions**:
- Check container logs
- Verify environment variables
- Check database connectivity
- Verify network connectivity

#### Migration Fails

**Symptoms**: Database migration fails

**Solutions**:
- Check database connection
- Verify migration file syntax
- Check for data conflicts
- Rollback migration if needed

---

## Appendix

### Useful Commands

#### GitHub Actions CLI

```bash
# List workflows
gh workflow list

# View workflow run
gh run view

# Re-run workflow
gh run rerun <run-id>
```

#### Amplify CLI

```bash
# View status
amplify status

# Publish
amplify publish

# Add environment
amplify env add
```

#### Docker Commands

```bash
# List images
docker images

# Pull image
docker pull <image>

# Run container
docker run -d <image>

# View logs
docker logs <container>
```

### References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS Amplify Documentation](https://docs.amplify.aws/)
- [Docker Documentation](https://docs.docker.com/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

---

**Note:** This CI/CD guide should be updated as the deployment process evolves and new requirements are identified.
