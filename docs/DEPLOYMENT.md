# StormGuard AI - Deployment Guide

## Environment Setup

### Development (Local)

1. **Clone Repository**
   ```bash
   git clone https://github.com/rafael-ceotto/StormGuard
   cd StormGuard
   ```

2. **Copy Environment File**
   ```bash
   cp .env.example .env
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Verify Services**
   ```bash
   # Check all containers running
   docker-compose ps
   
   # Check logs
   docker-compose logs -f airflow-webserver
   ```

---

## Production Deployment

### Prerequisites
- AWS Account with appropriate permissions
- Terraform installed
- kubectl configured
- Docker & Docker CLI

### Step 1: Infrastructure as Code

```bash
cd infra/terraform

# Configure AWS credentials
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file="prod.tfvars" -out=tfplan

# Apply
terraform apply tfplan
```

**What gets created:**
- EKS Kubernetes cluster
- RDS PostgreSQL (Aurora)
- ElastiCache Redis
- S3 Data Lake bucket
- CloudWatch log groups
- VPC, subnets, security groups

### Step 2: Build and Push Docker Images

```bash
# Configure Docker auth
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# Build images
docker build -f Dockerfile.api \
  -t ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/stormguard/api:latest .

docker build -f Dockerfile.airflow \
  -t ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/stormguard/airflow:latest .

# Push to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/stormguard/api:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/stormguard/airflow:latest
```

### Step 3: Deploy to Kubernetes

```bash
# Configure kubectl
aws eks update-kubeconfig --name stormguard-prod --region us-east-1

# Verify cluster access
kubectl cluster-info

# Create namespace
kubectl create namespace stormguard

# Create secrets
kubectl create secret generic stormguard-secrets \
  --from-literal=postgres-password='<your-password>' \
  --from-literal=minio-access-key='<key>' \
  --from-literal=minio-secret-key='<secret>' \
  -n stormguard

# Deploy infrastructure (postgres, redis, minio)
kubectl apply -f infra/kubernetes/configmaps.yaml
kubectl apply -f infra/kubernetes/deployments/postgres.yaml

# Deploy application
kubectl apply -f infra/kubernetes/deployments/api.yaml

# Verify deployment
kubectl get deployments -n stormguard
kubectl get services -n stormguard
kubectl get pods -n stormguard
```

### Step 4: Setup Monitoring

```bash
# Deploy Prometheus and Grafana
kubectl apply -f monitoring/prometheus.yml
kubectl apply -f monitoring/grafana.yml

# Get Grafana admin password
kubectl get secret -n stormguard grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode

# Port forward to access
kubectl port-forward -n stormguard svc/grafana 3000:80
# Open http://localhost:3000
```

### Step 5: Configure CI/CD

```bash
# Setup GitHub secrets
gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID"
gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY"
gh secret set DOCKER_REGISTRY_URL --body "$ECR_URL"

# Commit .github/workflows/ci-cd.yml
git add .github/workflows/ci-cd.yml
git commit -m "Add CI/CD pipeline"
git push origin main
```

---

## Configuration Management

### Environment Variables (Production)

Set these in AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name stormguard/prod \
  --secret-string '{
    "POSTGRES_PASSWORD": "secure-password",
    "REDIS_PASSWORD": "secure-password",
    "NOAA_API_KEY": "your-key",
    "NASA_API_KEY": "your-key",
    "AIRFLOW_WEBSERVER_SECRET_KEY": "secure-key"
  }'
```

### Database

Initialize RDS database:

```bash
# Get RDS endpoint
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)

# Connect and initialize
psql -h ${RDS_ENDPOINT} -U airflow -d airflow

# Create tables
\i database/schema.sql
```

---

## Scaling

### Horizontal Scaling (API)

```bash
# Scale API replicas
kubectl scale deployment stormguard-api \
  --replicas=5 \
  -n stormguard

# Check autoscaling (HPA)
kubectl get hpa -n stormguard

# Manual HPA
kubectl autoscale deployment stormguard-api \
  --min=3 \
  --max=10 \
  --cpu-percent=70 \
  -n stormguard
```

### Database Scaling

```bash
# Increase instance size
terraform apply -var="db_instance_class=db.r7g.2xlarge"

# Add read replicas
terraform apply -var="db_instance_count=3"
```

---

## Backup & Recovery

### Database Backup

```bash
# Create snapshot
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier stormguard-prod \
  --db-cluster-snapshot-identifier stormguard-backup-$(date +%s)

# Automated backups enabled (30 days retention)
```

### S3 Data Lake Backup

```bash
# Enable versioning (already done in Terraform)
# Enable replication
aws s3api put-bucket-replication \
  --bucket stormguard-datalake-prod \
  --replication-configuration file://replication.json
```

### Restore from Backup

```bash
# RDS restore
aws rds restore-db-cluster-from-snapshot \
  --db-cluster-identifier stormguard-prod-restored \
  --snapshot-identifier stormguard-backup-1708953600
```

---

## Troubleshooting Production Issues

### API Pod Crashing

```bash
# Check logs
kubectl logs -n stormguard deployment/stormguard-api --tail=100

# Check events
kubectl describe pod -n stormguard <pod-name>

# SSH into pod
kubectl exec -it -n stormguard <pod-name> -- /bin/bash
```

### Database Connection Issues

```bash
# Test connection
kubectl run -it --rm debug --image=postgres:15 --restart=Never \
  -- psql -h postgres-endpoint -U airflow

# Check RDS metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBClusterIdentifier,Value=stormguard-prod \
  --start-time 2024-02-26T00:00:00Z \
  --end-time 2024-02-27T00:00:00Z \
  --period 300 \
  --statistics Average
```

### Memory Pressure

```bash
# Check node resources
kubectl top nodes
kubectl top pods -n stormguard

# Increase pod limits
kubectl set resources deployment stormguard-api \
  --limits=memory=2Gi,cpu=1000m \
  --requests=memory=1Gi,cpu=500m \
  -n stormguard
```

---

## Upgrade Procedure

### Zero-Downtime Update

```bash
# 1. Build new image
docker build -f Dockerfile.api -t stormguard/api:v2.0 .

# 2. Push to registry
docker push stormguard/api:v2.0

# 3. Update deployment (rolling update)
kubectl set image deployment/stormguard-api \
  api=stormguard/api:v2.0 \
  -n stormguard --record

# 4. Monitor rollout
kubectl rollout status deployment/stormguard-api -n stormguard

# 5. Rollback if needed
kubectl rollout undo deployment/stormguard-api -n stormguard
```

---

## Cost Optimization

### AWS Cost Saving Tips

1. **Use Spot Instances**
   ```bash
   # Update node group to use spot
   aws ec2 describe-spot-price-history \
     --instance-types r6i.2xlarge \
     --region us-east-1
   ```

2. **Reserved Instances**
   - Purchase 1-year RI for databases
   - Reduces costs by ~40%

3. **S3 Lifecycle Policies**
   ```bash
   aws s3api put-bucket-lifecycle-configuration \
     --bucket stormguard-datalake-prod \
     --lifecycle-configuration file://lifecycle.json
   ```

4. **Resource Cleanup**
   ```bash
   # Delete unused resources
   terraform destroy -target=aws_elasticache_cluster.unused
   ```

---

## Security Hardening

### Enable HTTPS/TLS

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Enable ingress with TLS
kubectl apply -f infra/kubernetes/ingress-tls.yaml
```

### Network Policies

```bash
# Restrict traffic
kubectl apply -f infra/kubernetes/network-policies.yaml
```

### RBAC

```bash
# Create service accounts with least privilege
kubectl create serviceaccount stormguard-api -n stormguard
kubectl create role stormguard-api --verb=get,list,watch --resource=pods
kubectl create rolebinding stormguard-api \
  --clusterrole=view \
  --serviceaccount=stormguard:stormguard-api
```

---

## Monitoring & Alerting

### CloudWatch Metrics

```bash
# Custom metrics
aws cloudwatch put-metric-data \
  --namespace StormGuard \
  --metric-name PredictionLatency \
  --value 45.2 \
  --unit Milliseconds
```

### Setup PagerDuty Integration

```bash
# Add PagerDuty to Prometheus alertmanager
kubectl apply -f monitoring/alertmanager-pagerduty.yaml
```

---

## Compliance & Audit

### Enable CloudTrail Logging

```bash
aws cloudtrail create-trail \
  --name stormguard-audit \
  --s3-bucket-name stormguard-audit-logs
```

### Data Retention

Configured in terraform.tfvars:
```hcl
log_retention_days = 90  # 3 months
```

---

## Support & Maintenance

### Scheduled Maintenance Window

```bash
# Schedule during low traffic
# Sunday 3:00 AM UTC

kubectl patch deployment stormguard-api \
  -p '{"spec":{"template":{"metadata":{"annotations":{"deployment.kubernetes.io/revision":"2"}}}}}'
```

### Health Checks

```bash
# Daily health check script
kubectl apply -f monitoring/health-check-cronjob.yaml

# View recent checks
kubectl logs -n stormguard cronjob/health-check --tail=50
```

---

**Last Updated:** 2024-02-26  
**Maintainer:** Rafael Ceotto
