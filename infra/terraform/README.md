# Terraform Infrastructure

Complete Infrastructure-as-Code for StormGuard AI deployment on AWS.

## Quick Start

```bash
cd infra/terraform

# Configure AWS
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# Initialize
terraform init

# Plan
terraform plan -var-file="prod.tfvars"

# Apply
terraform apply -var-file="prod.tfvars"
```

## Files

- **main.tf** - Primary infrastructure resources
- **variables.tf** - Variable definitions
- **outputs.tf** - Export outputs
- **prod.tfvars** - Production configuration

## Resources Created

- EKS Kubernetes cluster
- RDS Aurora PostgreSQL
- ElastiCache Redis
- S3 Data Lake
- CloudWatch logs
- VPC and networking

## Outputs

After applying, outputs include:
- EKS cluster endpoint
- RDS endpoint
- Redis endpoint
- S3 bucket name

Retrieve with:
```bash
terraform output eks_cluster_name
terraform output rds_endpoint
```

## Destroy

```bash
terraform destroy -var-file="prod.tfvars"
```

⚠️ This will delete all resources including databases!
