# distributed-unet
Classifying EM-shower particles and track particles using Unet and Horovod  
Dataset available at: http://deeplearnphysics.org/Blog/2018-01-01-BrowsingSegmentationData_v0.1.0.html

### Note
This project exists because I wanted to fuse my work experience in data infrastructure and AWS with my interest in deep learning. That being said, this is just an exercise, and I have no actual need for data parallel training here (yet), because the dataset and model are small (u-net is actually intended for scenarios where limited data is available), and the segmentation problem for this data is easy.

### TODO / Improvements / Technical debt
- Create an issue for each point below and start addressing these.

#### Automation
- Configure some sort of method to allow a user to enter their API keys, so this project can be run by other people without difficulty.
- Add instructions for deploying and running this project.

#### Rate limiting
- This worker script will probably result in rate-limiting at scale, because it calls `DescribeInstancesInput` more times than necessary, instead of calling it once and caching the result. This means that when we launch all instances simultaneously, they will all make this API call numerous times, which may be throttled by AWS, causing some instances to fail.
- TODO: Store the output from `DescribeInstancesInput` in a dictionary instead of calling numerous times.
- TODO: Add a retry mechanism for failed API calls.

#### Fault tolerance
- This training method will probably fail if one of the instances fails.
- TODO: Consider using a defer mechanism to shut down the worker gracefully and relaunch a new one when something goes wrong.
- TODO: Communicate to the host the new IPs of replacement instances in case of failure.

#### Worker deployment
- I’m actually downloading the Go compiler and building on each instance right now, which is very much the wrong thing to do. Once I set up Jenkins and Artifactory, I plan to build the binary during CI, host it on Artifactory, and have the workers `wget` the binary in their user data script during initialization.
- TODO: Set up Artifactory and build the Go binary using Jenkins.
- TODO: If I eventually want to scale this up to a larger model and dataset, I should consider using Amazon FSx for Lustre to improve read/write speed to the local disk in each worker and to S3.
- TODO: Consider using Elastic Fabric Adapter to improve network speeds.

#### Modeling and distributed training
- I should not really use distributed data-parallel training here, because my dataset is small.
- The u-net model itself is actually intended to work on small datasets (specifically, it was built for biomedical data, where access to large datasets is limited), which is why it utilizes skip connections at different scales.
- TODO: Upgrade to a model that is harder to train and a dataset that is larger so I can actually get a realistic estimate of scaling efficiency using Horovod's implementation of ring-allreduce on EC2.
- TODO: Measure wall-clock-time to convergence, or conduct a scaling study and plot FLOPS (though this is definitely overkill).
- TODO: Consider not using TensorFlow and pivoting to PyTorch + Lightning instead.
- TODO: File format is in .npy, which is somewhat okay, but with larger datasets, potentially with multiple columns, consider using Petastorm and parquet.
- TODO: Explore different distribution strategies?
- TODO: Implement gradient compression to halve bandwidth between workers, potentially using float16 (assuming now over/underflow issues) or bfloat16's.
