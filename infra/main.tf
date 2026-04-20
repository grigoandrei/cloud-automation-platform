provider "aws" {
    region = "eusc-de-east-1"
}

resource "aws_ecr_repository" "my_ecr_repo"{
    name = "my-ecr-repo"
    image_tag_mutability = "MUTABLE"
    image_scanning_configuration {
      scan_on_push = true
    }
}

# IAM role for ECS task execution
resource "aws_iam_role" "ecs_task_execution" {
  name = "ecs-task-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws-eusc:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "Project VPC"
  }  
}

variable "private_subnet_cidrs" {
  type = list(string)
  description = "Private Subnet CIDR Values"
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

resource "aws_subnet" "private_subnets" {
  count = length(var.private_subnet_cidrs)
  vpc_id = aws_vpc.main.id
  cidr_block = element(var.private_subnet_cidrs, count.index)

  tags = {
   Name = "Private Subnet ${count.index + 1}"
 }
  
}

resource "aws_security_group" "ecs_security_group" {
  name = "ecs-sg"
  description = "Security group for ECS tasks"
  vpc_id = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  tags = {
    Name = "ecs-sg"
  }
  
}

resource "aws_security_group" "vpc_endpoints_security_group" {
  name = "vpc-endpoints-sg"
  description = "Security group for VPC Endpoints"
  vpc_id = aws_vpc.main.id

  ingress {
    description = "HTTPS"
    from_port = 443
    to_port = 443
    protocol = "tcp"
    security_groups = [aws_security_group.ecs_security_group.id]
  }

  tags = {
    Name = "vpc-endpoints-sg"
  }
  
}

resource "aws_ecs_cluster" "main" {
  name = "cloud-automation-cluster" 
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/cloud-automation-platform"
  retention_in_days = 7
}