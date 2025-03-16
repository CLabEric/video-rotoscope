#!/bin/bash
# Script to update effect code on S3 and EC2

set -e  # Exit on any error

# Configuration
S3_BUCKET="video-rotoscope-video"
EC2_INSTANCE_ID="i-09ff5c409d7ba31ce"  # Replace with your actual EC2 instance ID
REGION="us-east-1"  # Replace with your AWS region if different
TEMP_DIR="/tmp/effect-update-$(date +%s)"

# File mapping arrays (using separate arrays instead of associative array)
LOCAL_FILES=(
  "packages/backend/src/effects/neural/scanner_darkly.py"
  "packages/backend/src/effects/core/effect_core.py"
  "packages/backend/src/effects/processor.py"
)

S3_FILES=(
  "effects/neural/scanner_darkly.py"
  "effects/core/effect_core.py"
  "effects/processor.py"
)

EC2_PATHS=(
  "/tmp/video_effects/scanner_darkly.py"
  "/tmp/video_effects_core/effect_core.py"
  "/opt/video-processor/processor.py"
)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting effect code update process...${NC}"
mkdir -p $TEMP_DIR

# Track if any files were updated
UPDATED=false

# Step 1: Check and upload files to S3 if they differ
for i in "${!LOCAL_FILES[@]}"; do
    LOCAL_PATH="${LOCAL_FILES[$i]}"
    S3_PATH="${S3_FILES[$i]}"
    
    echo -e "${YELLOW}Checking ${LOCAL_PATH}...${NC}"
    
    # Download current S3 version to temp directory
    TEMP_FILE="${TEMP_DIR}/$(basename $LOCAL_PATH)"
    if aws s3 cp "s3://${S3_BUCKET}/${S3_PATH}" "${TEMP_FILE}" 2>/dev/null; then
        # Compare with local file
        if diff -q "${LOCAL_PATH}" "${TEMP_FILE}" >/dev/null; then
            echo -e "${GREEN}No changes detected for ${LOCAL_PATH}, skipping upload${NC}"
        else
            echo -e "${YELLOW}Changes detected in ${LOCAL_PATH}, uploading to S3...${NC}"
            aws s3 cp "${LOCAL_PATH}" "s3://${S3_BUCKET}/${S3_PATH}"
            UPDATED=true
        fi
    else
        echo -e "${YELLOW}File ${S3_PATH} doesn't exist in S3 or couldn't be downloaded, uploading...${NC}"
        aws s3 cp "${LOCAL_PATH}" "s3://${S3_BUCKET}/${S3_PATH}"
        UPDATED=true
    fi
done

# Step 2: If any files were updated, run commands on the EC2 instance
if [ "$UPDATED" = true ]; then
    echo -e "${YELLOW}Executing update commands on EC2 instance...${NC}"
    
    # Build commands to update each file on EC2
    COMMANDS="echo \"Starting effect code update on instance\"; "
    
    for i in "${!S3_FILES[@]}"; do
        S3_PATH="${S3_FILES[$i]}"
        EC2_PATH="${EC2_PATHS[$i]}"
        # Create directory if needed
        DIR=$(dirname "$EC2_PATH")
        COMMANDS+="mkdir -p $DIR; "
        # Download file from S3
        COMMANDS+="aws s3 cp s3://$S3_BUCKET/$S3_PATH $EC2_PATH; "
        # Set permissions
        COMMANDS+="chmod 755 $EC2_PATH; "
    done
    
    # Restart service
    COMMANDS+="sudo systemctl restart video-processor.service; "
    COMMANDS+="echo \"Update completed successfully\""
    
	# Execute commands on instance with properly escaped JSON
	aws ssm send-command \
	--instance-ids $EC2_INSTANCE_ID \
	--document-name "AWS-RunShellScript" \
	--region $REGION \
	--parameters '{
		"commands":[
		"echo \"Starting effect code update on instance\"",
		"mkdir -p /tmp/video_effects",
		"sudo aws s3 cp s3://'"$S3_BUCKET"'/effects/neural/scanner_darkly.py /tmp/video_effects/scanner_darkly.py",
		"sudo chmod 755 /tmp/video_effects/scanner_darkly.py",
		"mkdir -p /tmp/video_effects_core",
		"sudo aws s3 cp s3://'"$S3_BUCKET"'/effects/core/effect_core.py /tmp/video_effects_core/effect_core.py",
		"sudo chmod 755 /tmp/video_effects_core/effect_core.py",
		"mkdir -p /opt/video-processor",
		"sudo aws s3 cp s3://'"$S3_BUCKET"'/effects/processor.py /opt/video-processor/processor.py",
		"sudo chmod 755 /opt/video-processor/processor.py",
		"sudo systemctl restart video-processor.service",
		"echo \"Update completed successfully\""
		]
	}' \
	--output text
    
    echo -e "${GREEN}Update commands sent to instance. Updates should be applied shortly.${NC}"
else
    echo -e "${GREEN}No files needed updating. No commands sent to EC2 instance.${NC}"
fi

# Clean up
rm -rf $TEMP_DIR

echo -e "${YELLOW}Note: To confirm success, check the service logs on the EC2 instance with:${NC}"
echo -e "  sudo tail -f /var/log/video-processor.log"