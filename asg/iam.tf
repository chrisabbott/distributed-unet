resource "aws_iam_role" "s3_rw_role" {
  name = "s3_rw_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "sts:AssumeRole"
      ],
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_policy" "s3_rw_policy" {
  name = "s3_rw_policy"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListObjects"
      ],
      "Resource": "arn:aws:s3:::dlp-semseg"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::dlp-semseg/*"
    }
  ]
}
EOF
}

resource "aws_iam_policy_attachment" "s3_rw_attachment" {
  name       = "s3_rw_attachment"
  roles      = ["${aws_iam_role.s3_rw_role.name}"]
  policy_arn = "${aws_iam_policy.s3_rw_policy.arn}"
}

resource "aws_iam_instance_profile" "s3_rw_profile" {
  name = "s3_rw_profile"
  role = "${aws_iam_role.s3_rw_role.name}"
}
