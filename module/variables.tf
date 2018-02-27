# variable "spark_webhook_url" {
#   type = "string"
# }

variable "spark_channel_map" {
  type = "string"
}

variable "lambda_function_name" {
  type = "string"
  default = "sns-to-spark"
}

variable "default_username" {
  type = "string"
  default = "AWS Lambda"
}

variable "default_channel" {
  type = "string"
  default = ""
}

variable "default_emoji" {
  type = "string"
  default = ":information_source:"
}

variable "lambda_iam_role_name" {
  type = "string"
  default = "lambda-sns-to-spark"
}

variable "lambda_iam_policy_name" {
  type = "string"
  default = "lambda-sns-to-spark-policy"
}


variable "spark_bearer_token" {
  type = "string"
}
