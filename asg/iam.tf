resource "aws_iam_role" "s3_ec2_role" {
  name = "s3_ec2_role"
  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "sts:AssumeRole"
            ],
            "Principal": {
                "Service": [
                    "ec2.amazonaws.com",
                    "s3.amazonaws.com"
                ]
            }
        }
    ]
}
EOF
}

resource "aws_iam_policy" "s3_ec2_policy" {
  name = "s3_ec2_policy"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket",
                "s3:GetObjectVersion"
            ],
            "Resource": [
                "arn:aws:s3:::lartpc-semantic-segmentation",
                "arn:aws:s3:::lartpc-semantic-segmentation/*.npy"
            ]
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "s3:*"
            ],
            "Resource": [
                "arn:aws:s3:::chrisabbott-public-keys",
                "arn:aws:s3:::chrisabbott-public-keys/*.pub"
            ]
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "autoscaling:DeleteTags",
                "autoscaling:DescribeAutoScalingInstances",
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:CreateOrUpdateTags",
                "autoscaling:DescribePolicies",
                "autoscaling:DescribeTags",
                "ec2:DeleteTags",
                "ec2:DescribeInstances",
                "ec2:CreateTags"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

resource "aws_iam_policy_attachment" "s3_ec2_attachment" {
  name       = "s3_ec2_attachment"
  roles      = ["${aws_iam_role.s3_ec2_role.name}"]
  policy_arn = "${aws_iam_policy.s3_ec2_policy.arn}"
}

resource "aws_iam_instance_profile" "s3_ec2_profile" {
  name = "s3_ec2_profile"
  role = "${aws_iam_role.s3_ec2_role.name}"
}
