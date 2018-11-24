#####
# Lambda functions
#

resource "aws_lambda_function" "sns_to_webex_teams" {
  filename = "${path.module}/lambda/sns-to-webex-teams.zip"
  function_name = "${var.lambda_function_name}"
  role = "${aws_iam_role.lambda_sns_to_webex_teams.arn}"
  handler = "lambda_function.lambda_handler"
  source_code_hash = "${base64sha256(file("${path.module}/lambda/sns-to-webex-teams.zip"))}"
  runtime = "python2.7"

  environment {
    variables = {
      CHANNEL_MAP = "${base64encode("${var.webex_teams_channel_map}")}"
      DEFAULT_USERNAME = "${var.default_username}"
      DEFAULT_CHANNEL = "${var.default_channel}"
      DEFAULT_EMOJI = "${var.default_emoji}"
      WEBEX_TEAMS_TOKEN = "${var.webex_teams_bearer_token}"
    }
  }
}
