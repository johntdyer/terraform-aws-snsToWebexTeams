#####
# IAM roles
#

resource "aws_iam_role" "lambda_sns_to_webex_teams" {
  name = "${var.lambda_iam_role_name}"
  assume_role_policy = "${file("${path.module}/policies/lambda-assume-role.json")}"
}

#####
# IAM policies
#

resource "aws_iam_role_policy" "lambda_sns_to_webex_teams" {
  name = "${var.lambda_iam_policy_name}"
  role = "${aws_iam_role.lambda_sns_to_webex_teams.id}"
  policy = "${file("${path.module}/policies/lambda-role-policy.json")}"
}
