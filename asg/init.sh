#!/bin/bash

function clone_repo {
  echo "Cloning chrisabbott/MultiNodeUnet"

  cd /home/ubuntu/ && git clone -b tf_config https://github.com/chrisabbott/MultiNodeUnet.git
  chmod 777 /home/ubuntu/MultiNodeUnet
}

function bash_is_from_the_80s {
  echo "Installing go"
  wget https://dl.google.com/go/go1.13.4.linux-amd64.tar.gz && \
  tar -C /usr/local -xzf go1.13.4.linux-amd64.tar.gz
  echo "export PATH=$PATH:/usr/local/go/bin" >> /etc/profile
  source /etc/profile
}

function build_and_run_worker {
  echo "Building and running worker"
  cd /home/ubuntu/MultiNodeUnet
  go build asg/worker.go && ./worker
}

function setup {
  clone_repo
  bash_is_from_the_80s
  build_and_run_worker
}

setup
