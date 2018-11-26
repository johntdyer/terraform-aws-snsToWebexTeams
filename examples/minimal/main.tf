#####
# Providers
#

provider "aws" {
  region = "${var.region}"
}

#####
# Modules
#

module "sns_to_webex_teams" {
  source = "../.."
  webex_teams_channel_map = "${var.webex_teams_channel_map}"
  webex_teams_bearer_token = "${var.webex_teams_bearer_token}"
}

#####
# CloudWatch Alarms
#

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name = "lambda-duration"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods = "2"
  metric_name = "Duration"
  namespace = "AWS/Lambda"
  period = "300"
  extended_statistic = "p95"

  threshold = "5000"
  alarm_description = "This metric monitors AWS Lambda duration"

  alarm_actions = [
    "${aws_sns_topic.production_notices.arn}"
  ]

  ok_actions = [
    "${aws_sns_topic.production_notices.arn}"
  ]
}

#####
# SNS Topics
#

resource "aws_sns_topic" "production_notices" {
  name = "production-notices"
}

#####
# SNS Subscriptions
#

resource "aws_lambda_permission" "allow_lambda_sns_to_webex_teams" {
  statement_id = "AllowSNSToWebexTeamsExecutionFromSNS"
  action = "lambda:invokeFunction"
  function_name = "${module.sns_to_webex_teams.lambda_function_arn}"
  principal = "sns.amazonaws.com"
  source_arn = "${aws_sns_topic.production_notices.arn}"
}

resource "aws_sns_topic_subscription" "lambda_sns_to_webex_teams" {
  topic_arn = "${aws_sns_topic.production_notices.arn}"
  protocol = "lambda"
  endpoint = "${module.sns_to_webex_teams.lambda_function_arn}"
}
