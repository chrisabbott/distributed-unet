# Create data folders
mkdir ./data
aws s3 cp s3://dlp-semseg/ ./data --recursive

# Setup virtualenv and install packages
virtualenv -p python3 .venv && source .venv/bin/activate
pip3 install -r requirements.txt
