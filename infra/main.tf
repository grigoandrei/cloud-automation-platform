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