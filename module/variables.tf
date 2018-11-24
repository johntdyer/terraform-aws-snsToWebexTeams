# variable "webex_teamswebhook_url" {
#   type = "string"
# }

variable "webex_teams_channel_map" {
  type = "string"
}

variable "lambda_function_name" {
  type = "string"
  default = "sns-to-webex-teams"
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
  default = "lambda-sns-to-webex-teams"
}

variable "lambda_iam_policy_name" {
  type = "string"
  default = "lambda-sns-to-webex-teams-policy"
}


variable "webex_teams_bearer_token" {
  type = "string"
}
