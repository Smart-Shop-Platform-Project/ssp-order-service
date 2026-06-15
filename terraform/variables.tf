variable "aws_region" { type = string; default = "us-east-1" }
variable "environment" { type = string }
variable "container_image" { type = string; default = "placeholder" }

variable "kafka_broker_url_param_name" {
  type        = string
  description = "The name of the SSM parameter for the Kafka broker URL."
  default     = "ssp/shared/kafka_broker_url"
}
