# Cloud Automation Platform

A lightweight cloud automation toolkit for deploying and managing containerized applications on AWS ECS Fargate.

## What it does

- **FastAPI metrics API** — exposes health checks and system metrics (CPU, RAM, disk, load average, network I/O)
- **Deploy CLI** — builds, saves, and pushes container images to AWS ECR using Podman or Docker
- **Scaling script** — monitors ECS tasks via CloudWatch metrics and scales based on CPU/memory utilization
- **Infrastructure as Code** — Terraform config for ECR, ECS Fargate, VPC, subnets, and security groups

## Project structure

```
cloud-automation-platform/
├── app/
│   └── api.py              # FastAPI app with /health and /data endpoints
├── docker/
│   └── Dockerfile           # Container image definition
├── scripts/
│   ├── deploy.py            # CLI for build, save, push, and deploy
│   ├── scale.py             # ECS auto-scaling based on CloudWatch metrics
│   └── errors.py            # AWS error formatting utilities
├── infra/
│   └── main.tf              # Terraform infrastructure (ECR, ECS, VPC, IAM)
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the API locally

```bash
uvicorn app.api:app --reload
```

Endpoints:
- `GET /health` — returns `{"status": "OK"}`
- `GET /data` — returns system metrics (CPU, RAM, disk, load average, network I/O)

## Deploy CLI

Build, save, push, or run the full deploy pipeline:

```bash
python scripts/deploy.py build
python scripts/deploy.py save
python scripts/deploy.py push
python scripts/deploy.py deploy          # build + push
```

All commands support `--dry-run`, `--verbose`, and `--help`:

```bash
python scripts/deploy.py deploy --dry-run
python scripts/deploy.py push --ecr-repo my-ecr-repo --region eusc-de-east-1
```

## Infrastructure

Provision AWS resources with Terraform:

```bash
cd infra
terraform init
terraform apply
```

Creates: ECR repository, ECS cluster, Fargate service/task, VPC, private subnets, and security groups.

## Requirements

- Python 3.12+
- Podman or Docker
- AWS CLI (configured with credentials)
- Terraform
