#####
# Lambda functions
#

resource "aws_lambda_function" "sns_to_spark" {
  filename = "${path.module}/lambda/sns-to-spark.zip"
  function_name = "${var.lambda_function_name}"
  role = "${aws_iam_role.lambda_sns_to_spark.arn}"
  handler = "lambda_function.lambda_handler"
  source_code_hash = "${base64sha256(file("${path.module}/lambda/sns-to-spark.zip"))}"
  runtime = "python2.7"

  environment {
    variables = {
      CHANNEL_MAP = "${base64encode("${var.spark_channel_map}")}"
      DEFAULT_USERNAME = "${var.default_username}"
      DEFAULT_CHANNEL = "${var.default_channel}"
      DEFAULT_EMOJI = "${var.default_emoji}"
      SPARK_TOKEN = "${var.spark_bearer_token}"
    }
  }
}
