package main

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/autoscaling"
	"github.com/aws/aws-sdk-go/service/ec2"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
	"golang.org/x/crypto/ssh"
	"io/ioutil"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"syscall"
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

func constructHorovodrunCommand(sess *session.Session, ids []string, perInstanceGpus int, command string) string {
	totalGpus := len(ids) * perInstanceGpus
	horovodRun := fmt.Sprintf("/home/ubuntu/anaconda3/envs/tensorflow_p36/bin/horovodrun -np %v -H localhost:%v", totalGpus, perInstanceGpus)
	thisInstanceIPv4 := getThisInstanceMetadata("local-ipv4")
	for _, instanceId := range ids {
		privateIPv4 := getInstancePrivateIp(describeInstanceById(sess, instanceId))
		if privateIPv4 != thisInstanceIPv4 {
			horovodRun += fmt.Sprintf(",%v:%v", privateIPv4, perInstanceGpus)
		}
	}
	horovodRun += fmt.Sprintf(" %v", command)
	return horovodRun
}

func describeInstanceById(sess *session.Session, id string) *ec2.DescribeInstancesOutput {
	svc := ec2.New(sess)
	input := &ec2.DescribeInstancesInput{
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

func disableStrictHostKeyChecking(leaderIPv4 string) {
	writeToFile(
		"/home/ubuntu/.ssh/config",
		fmt.Sprintf("Host ubuntu@%s\n    StrictHostKeyChecking no\n", leaderIPv4),
		syscall.O_APPEND|syscall.O_CREAT|syscall.O_RDWR,
		0644)
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
			Key:    aws.String(key),
		})
	if err != nil {
		exitErrorf("Unable to download item %q, %v\n", key, err)
	}
	fmt.Println("Downloaded", file.Name(), numBytes, "bytes")
}

// encodePrivateKeyToPEM encodes Private Key from RSA to PEM format
func encodePrivateKeyToPEM(privateKey *rsa.PrivateKey) []byte {
	// Get ASN.1 DER format
	privDER := x509.MarshalPKCS1PrivateKey(privateKey)

	// pem.Block
	privBlock := pem.Block{
		Type:    "RSA PRIVATE KEY",
		Headers: nil,
		Bytes:   privDER,
	}

	// Private key in PEM format
	privatePEM := pem.EncodeToMemory(&privBlock)
	return privatePEM
}

func exitErrorf(msg string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, msg, args...)
	os.Exit(1)
}

func find(slice []string, val string) (int, bool) {
	for i, item := range slice {
		if item == val {
			return i, true
		}
	}
	return -1, false
}

// generatePrivateKey creates a RSA Private Key of specified byte size
// https://gist.github.com/devinodaniel/8f9b8a4f31573f428f29ec0e884e6673
func generatePrivateKey(bitSize int) *rsa.PrivateKey {
	// Private Key generation
	privateKey, err := rsa.GenerateKey(rand.Reader, bitSize)
	if err != nil {
		exitErrorf("Failed to generate ssh private key")
	}

	// Validate Private Key
	err = privateKey.Validate()
	if err != nil {
		exitErrorf("Failed to validate ssh private key")
	}

	fmt.Println("Private Key generated")
	return privateKey
}

// generatePublicKey take a rsa.PublicKey and return bytes suitable for writing to .pub file
// returns in the format "ssh-rsa ..."
// https://gist.github.com/devinodaniel/8f9b8a4f31573f428f29ec0e884e6673
func generatePublicKey(privatekey *rsa.PublicKey) []byte {
	publicRsaKey, err := ssh.NewPublicKey(privatekey)
	if err != nil {
		exitErrorf("Failed to generate ssh public key")
	}

	pubKeyBytes := ssh.MarshalAuthorizedKey(publicRsaKey)

	fmt.Println("Public key generated")
	return pubKeyBytes
}

func generateSshKeys() {
	bitSize := 4096
	idRsaPub := "/home/ubuntu/.ssh/id_rsa.pub"
	idRsa := "/home/ubuntu/.ssh/id_rsa"
	privateKey := generatePrivateKey(bitSize)
	publicKey := generatePublicKey(&privateKey.PublicKey)
	privateKeyBytes := encodePrivateKeyToPEM(privateKey)
	writeToFile(idRsaPub, string(publicKey), syscall.O_RDWR|syscall.O_CREAT, 0644)
	writeToFile(idRsa, string(privateKeyBytes), syscall.O_RDWR|syscall.O_CREAT, 0644)
}

func getPublicKeys(sess *session.Session, bucket string) {
	svc := s3.New(sess)
	downloader := s3manager.NewDownloader(sess)
	params := &s3.ListObjectsInput {
  	Bucket: aws.String(bucket),
	}

	dest := "keys/"
	os.Mkdir(dest, os.FileMode(0777))

	resp, _ := svc.ListObjects(params)
	for _, key := range resp.Contents {
		downloadObjectFromS3(bucket, *key.Key, dest, downloader)
	}
}

func getInstancePrivateIp(metadata *ec2.DescribeInstancesOutput) string {
	return string(*metadata.Reservations[0].Instances[0].PrivateIpAddress)
}

func getLeaderId(sess *session.Session, asg_name string) string {
	/*
		 The leader (worker 0) will be chosen by sorting instance IDs by string and taking the zeroth element.
	*/
	if os.Getenv("LEADER") == "" {
		instanceIds := listAsgInstanceIds(sess, asg_name)
		sort.Strings(instanceIds)
		os.Setenv("LEADER", instanceIds[0])
	}
	return os.Getenv("LEADER")
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

func getThisInstanceMetadata(key string) string {
	var client = &http.Client{
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

func listAsgInstances(sess *session.Session, asg_name string) []*autoscaling.Instance {
	svc := autoscaling.New(sess)
	input := &autoscaling.DescribeAutoScalingGroupsInput{
		AutoScalingGroupNames: []*string{
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
	input := &ec2.CreateTagsInput{
		Resources: []*string{
			aws.String(id),
		},
		Tags: []*ec2.Tag{
			{
				Key:   aws.String("state"),
				Value: aws.String(state),
			},
		},
	}

	_, err := svc.CreateTags(input)
	if err != nil {
		exitErrorf("Failed to set state tag: %s\n", state)
	}
}

func uploadFileToS3(sess *session.Session, abspath string, key string, bucket string) {
	file, err := os.Open(abspath)
	defer file.Close()
	uploader := s3manager.NewUploader(sess)
	result, err := uploader.Upload(&s3manager.UploadInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
		Body:   file,
	})
	if err != nil {
		exitErrorf("Failed to upload %s\n", abspath)
	} else {
		fmt.Printf("Uploaded %s to %s", abspath, result.Location)
	}
}

func writeToFile(abspath string, text string, mode int, permissions os.FileMode) {
	f, err := os.OpenFile(abspath, mode, permissions)
	if err != nil {
		fmt.Println(err)
	}
	defer f.Close()
	if _, err := f.WriteString(text); err != nil {
		fmt.Println(err)
	}
}

func main() {
	sess, _ := session.NewSession(&aws.Config{
		Region: aws.String("us-east-1")},
	)

	// Master must wait for this instance to finish initializing
	setStateTag(sess, getThisInstanceMetadata("instance-id"), "not-ready")
	asgName := "unet-training-cluster"
	myId := getThisInstanceMetadata("instance-id")
	myIPv4 := getThisInstanceMetadata("public-ipv4")
	myLocalIPv4 := getThisInstanceMetadata("local-ipv4")
	fmt.Printf("My ID: %s\n", myId)
	fmt.Printf("My Public IPv4: %s\n", myIPv4)
	fmt.Printf("My Local IPv4: %s\n", myLocalIPv4)

	// Download datasets
	data := downloadDatasetFromS3(sess)
	changePermissions(data, 0777)

	// Leader election
	leaderId := getLeaderId(sess, asgName)
	leaderIPv4 := getInstancePrivateIp(describeInstanceById(sess, leaderId))
	fmt.Printf("Leader ID: %s\n", leaderId)
	fmt.Printf("Leader private IPv4: %s\n", leaderIPv4)

	// Generate ssh keys
	generateSshKeys()

	// Disable StrictHostKeyChecking for the leader
	disableStrictHostKeyChecking(leaderIPv4)

	// Upload public key
	uploadFileToS3(sess, "/home/ubuntu/.ssh/id_rsa.pub", fmt.Sprintf("%s.pub", myId), "chrisabbott-public-keys")

	// Ready to go
	setStateTag(sess, myId, "ready")

	// Wait until all instances have uploaded their keys
	for {
		_, found := find(listAsgInstanceStates(sess, asgName), "not-ready")
		if !found {
			getPublicKeys(sess, "chrisabbott-public-keys")
			items, _ := ioutil.ReadDir("keys/")
			for _, item := range items {
				content, _ := ioutil.ReadFile(fmt.Sprintf("%s%s", "keys/", item.Name()))
				writeToFile("~/.ssh/authorized_keys", fmt.Sprintf("%s\n", string(content)), syscall.O_CREAT|syscall.O_APPEND|syscall.O_RDWR, 0777)
			}
			break
		}
	}

	// Begin polling all instances for their state
	if myId == leaderId {
		setStateTag(sess, myId, "ready, leader")
		for {
			_, found := find(listAsgInstanceStates(sess, asgName), "not-ready")
			if !found {
				// Last index returned because "not-ready" not found in instanceStates, so all instances
				// are ready to go
				break
			}
			time.Sleep(5 * time.Second)
			fmt.Println("Waiting for all instances to enter a ready state ...")
		}
		fmt.Printf("All instances are ready: %s\n", listAsgInstanceStates(sess, asgName))
		// horovodrun -np 2 -H localhost:1, ec2-34-232-70-101.compute-1.amazonaws.com:1 python3 unet.py -X data/train_X.npy -y data/train_y.npy -l INFO -o models
		horovodRun := constructHorovodrunCommand(sess, listAsgInstanceIds(sess, asgName), 1,
			"python3 unet.py -X data/train_X.npy -y data/train_y.npy -l INFO -o models train")
		fmt.Println(horovodRun)
		cmd := exec.Command(horovodRun)
		cmd.Run()
	}
}
