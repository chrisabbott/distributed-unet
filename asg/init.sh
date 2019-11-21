#!/bin/bash

function my_instance_id {
  # Magic EC2 url
  curl -qs --connect-timeout 3 http://169.254.169.254/latest/meta-data/instance-id
}

function my_region {
  # Magic EC2 url
  curl -qs --connect-timeout 3 http://169.254.169.254/latest/dynamic/instance-identity/document | jq .region -r
}

function my_asg_name {
  aws autoscaling describe-auto-scaling-instances --region "$(my_region)" \
  --instance-ids $(my_instance_id) --query 'AutoScalingInstances[*].AutoScalingGroupName' --output text
}

function clone_repo {
  echo "Cloning chrisabbott/MultiNodeUnet"

  cd /home/ubuntu/ && git clone https://github.com/chrisabbott/MultiNodeUnet.git
}

function install_apt_packages {
  echo "Installing apt packages"

  # Install curl and jq for parsing ASG variables
  apt-get clean
  apt-get update -y
  apt-get install -y curl jq
}

function pull_dataset {
  echo "Pulling LArTPC semantic segmentation dataset from S3"

  # Create data folders
  mkdir /home/ubuntu/data
  aws s3 cp s3://dlp-semseg/ /home/ubuntu/data --recursive
  chmod -r 777 /home/ubuntu/data
}

function set_up_environment {
  echo "Initialize conda and install requirements.txt"

  # Setup virtualenv and install packages
  source activate tensorflow_p36
  cd /home/ubuntu/MultiNodeUnet
  pip3 install -r dlami_requirements.txt
}

function terminate {
  echo "Failed to initialize instance"

  status="ABANDON"
  instance_id="$(my_instance_id)"
  region="$(my_region)"
  asg_name="$(my_asg_name)"

  aws autoscaling complete-lifecycle-action --lifecycle-hook-name terminate_unhealthy_init \
  --auto-scaling-group-name "$asg_name" --instance-id "$instance_id" \
  --lifecycle-action-result "$status" --region "$region"
  echo "Lifecycle status ABANDON. Terminated instance '$instance_id'"
}

function setup {
  #trap terminate ERR

  install_apt_packages
  clone_repo
  pull_dataset
  set_up_virtualenv
}

setup
