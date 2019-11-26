#!/bin/bash

function clone_repo {
  echo "Cloning chrisabbott/MultiNodeUnet"

  cd /home/ubuntu/ && git clone https://github.com/chrisabbott/MultiNodeUnet.git
  chmod 777 /home/ubuntu/MultiNodeUnet
}

function install_go {
  echo "Installing go"
  wget -q https://dl.google.com/go/go1.13.4.linux-amd64.tar.gz && \
  tar -C /usr/local -xzf go1.13.4.linux-amd64.tar.gz
  echo "export PATH=$PATH:/usr/local/go/bin" >> /etc/profile
  echo "export GOPATH=/home/ubuntu/go" >> /etc/profile
  echo "export GOCACHE=/home/ubuntu/.cache" >> /etc/profile
  source /etc/profile
  mkdir -p "$GOCACHE" "$GOPATH/src" "$GOPATH/bin" && chmod -R 777 "$GOPATH" "$GOCACHE"
}

function build_and_run_worker {
  echo "Building and running worker"
  cd /home/ubuntu/MultiNodeUnet
  go get github.com/aws/aws-sdk-go/...
  go get -u golang.org/x/crypto/...
  go build asg/worker.go && touch ./init.out && ./worker > ./init.out
}

function setup {
  clone_repo
  install_go
  build_and_run_worker
}

setup
