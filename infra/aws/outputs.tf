output "incidents_queue_url" {
  value = aws_sqs_queue.incidents.url
}

output "incidents_queue_arn" {
  value = aws_sqs_queue.incidents.arn
}

output "dlq_queue_arn" {
  value = aws_sqs_queue.incidents_dlq.arn
}
