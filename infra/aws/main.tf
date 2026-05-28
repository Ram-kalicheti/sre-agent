terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_sqs_queue" "incidents_dlq" {
  name                      = "${var.project}-incidents-dlq"
  message_retention_seconds = 1209600

  tags = {
    project     = var.project
    environment = var.environment
  }
}

resource "aws_sqs_queue" "incidents" {
  name                       = "${var.project}-incidents"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.incidents_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    project     = var.project
    environment = var.environment
  }
}
