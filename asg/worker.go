package main

import (
  //"encoding/json"
	"fmt"
  "github.com/aws/aws-sdk-go/aws"
  "github.com/aws/aws-sdk-go/aws/session"
  "github.com/aws/aws-sdk-go/service/autoscaling"
  "github.com/aws/aws-sdk-go/service/ec2"
  "github.com/aws/aws-sdk-go/service/s3"
  "github.com/aws/aws-sdk-go/service/s3/s3manager"
  "io/ioutil"
  "net/http"
  "os"
  "path/filepath"
  "sort"
  "time"
)

func changePermissions(dir string, code uint) {
  err := os.Chmod(dir, os.FileMode(code))
  if err != nil {
    exitErrorf("Failed to modify permissions: %s\n", err)
  } else {
    fmt.Printf("Modified permissions of %s to %v\n", dir, os.FileMode(code))
  }
}

func describeInstanceById(sess *session.Session, id string) *ec2.DescribeInstancesOutput {
  svc := ec2.New(sess)
  input := &ec2.DescribeInstancesInput {
    Filters: []*ec2.Filter{
      &ec2.Filter{
        Name: aws.String("instance-id"),
        Values: []*string{
          aws.String(id),
        },
      },
    },
  }

  res, err := svc.DescribeInstances(input)
  if err != nil {
    exitErrorf("Failed to describe instances: %s\n", err)
  }
  return res
}

func downloadDatasetFromS3(sess *session.Session) string {
  // Pull the dataset from S3
  fmt.Println("Downloading dataset")
  downloader := s3manager.NewDownloader(sess)

  // DeepLearnPhysics.org semantic segmentation dataset
  bucket := "lartpc-semantic-segmentation"
  files := []string{"train_X.npy", "train_y.npy", "test_X.npy", "test_y.npy"}
  dest := "data/"
  os.Mkdir(dest, os.FileMode(0777))

  for _, key := range files {
    downloadObjectFromS3(bucket, key, dest, downloader)
  }
  return dest
}

func downloadObjectFromS3(bucket string, key string, dest string, downloader *s3manager.Downloader) {
  // Create file on host os
  file, err := os.Create(filepath.Join(dest, key))
  if err != nil {
    exitErrorf("Unable to open file %q, %v\n", err)
  }
  defer file.Close()

  // Download from S3
  numBytes, err := downloader.Download(file,
    &s3.GetObjectInput{
      Bucket: aws.String(bucket),
      Key: aws.String(key),
    })
  if err != nil {
    exitErrorf("Unable to download item %q, %v\n", key, err)
  }
  fmt.Println("Downloaded", file.Name(), numBytes, "bytes")
}

func getInstance0(sess *session.Session, asg_name string) string {
  /*
    Worker 0 will be chosen by sorting instance IDs by string and taking the zeroth element.
  */
  if os.Getenv("WORKER_0") == "" {
    instance_ids := listAsgInstanceIds(sess, asg_name)
    sort.Strings(instance_ids)
    os.Setenv("WORKER_0", instance_ids[0])
  }
  return os.Getenv("WORKER_0")
}

func getThisInstanceMetadata(key string) string {
  var client = &http.Client {
    Timeout: time.Second * 10,
  }
  url := "http://169.254.169.254/latest/meta-data/" + key
  errMsg := "Error getting instance metadata"
  res, err := client.Get(url)
  if err != nil {
    exitErrorf("%s: %s\n", errMsg, err)
  }
  defer res.Body.Close()

  bodyBytes, err := ioutil.ReadAll(res.Body)
  if err != nil {
    exitErrorf(errMsg, err)
  }
  return string(bodyBytes)
}

func getStateTag(metadata *ec2.DescribeInstancesOutput) string {
  tags := metadata.Reservations[0].Instances[0].Tags
  state := "None"
  for _, tag := range tags {
    if *tag.Key == "state" {
      return *tag.Value
    }
  }
  return state
}

func exitErrorf(msg string, args ...interface{}) {
  fmt.Fprintf(os.Stderr, msg, args...)
  os.Exit(1)
}

func listAsgInstances(sess *session.Session, asg_name string) []*autoscaling.Instance {
  svc := autoscaling.New(sess)
  input := &autoscaling.DescribeAutoScalingGroupsInput {
    AutoScalingGroupNames: []*string {
      aws.String(asg_name),
    },
  }

  res, err := svc.DescribeAutoScalingGroups(input)
  if err != nil {
    exitErrorf("Failed to describe ASG: %s\n", err)
  }
  if len(res.AutoScalingGroups) <= 0 {
    exitErrorf("No ASG found.\n")
  }
  return res.AutoScalingGroups[0].Instances
}

func listAsgInstanceIds(sess *session.Session, asg_name string) []string {
  var list []string
  for _, instance := range listAsgInstances(sess, asg_name) {
    list = append(list, *instance.InstanceId)
  }
  return list
}

func listAsgInstanceStates(sess *session.Session, asg_name string) []string {
  var list []string
  for _, id := range listAsgInstanceIds(sess, asg_name) {
    list = append(list, getStateTag(describeInstanceById(sess, id)))
  }
  return list
}

func setStateTag(sess *session.Session, id string, state string) {
  svc := ec2.New(sess)
  input := &ec2.CreateTagsInput {
    Resources: []*string {
      aws.String(id),
    },
    Tags: []*ec2.Tag {
      {
        Key: aws.String("state"),
        Value: aws.String(state),
      },
    },
  }

  _, err := svc.CreateTags(input)
  if err != nil {
    exitErrorf("Failed to set state tag: %s\n", state)
  }
}

func main() {
  sess, _ := session.NewSession(&aws.Config{
    Region: aws.String("us-east-1")},
  )

  // Download datasets
  data := downloadDatasetFromS3(sess)
  changePermissions(data, 0777)

  // Get instance data
  instanceIds := listAsgInstanceIds(sess, "unet-training-cluster")
  fmt.Println(instanceIds)
  fmt.Println("ID: " + getThisInstanceMetadata("instance-id"))
  fmt.Println("Public IPv4: " + getThisInstanceMetadata("public-ipv4"))
  fmt.Println("Local IPv4: " + getThisInstanceMetadata("local-ipv4"))
}
