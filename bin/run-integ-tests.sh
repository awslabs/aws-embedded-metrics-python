#!/usr/bin/env bash
#
# Run integration tests against a CW Agent.
# 
# usage:
#   export AWS_ACCESS_KEY_ID=
#   export AWS_SECRET_ACCESS_KEY=
#   export AWS_REGION=us-west-2
#   ./run-integ-tests.sh

rootdir=$(git rev-parse --show-toplevel)
rootdir=${rootdir:-$(pwd)} # in case we are not in a git repository (Code Pipelines)

tempfile="$rootdir/tests/integ/agent/.temp"
status_code=0

###################################
# Configure and start the agent
###################################

# Check if IAM user credentials exist
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "No IAM user credentials found, assuming we are running on CodeBuild pipeline, falling back to IAM role..."
    
    # Store the AWS STS assume-role output and extract credentials
    CREDS=$(aws sts assume-role \
        --role-arn $Code_Build_Execution_Role_ARN \
        --role-session-name "session-$(uuidgen)" \
        --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
        --output text \
        --duration-seconds 3600)

    # Parse the output into separate variables
    read AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN <<< $CREDS

    # Export the variables
    export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
else
    echo "Using provided IAM user credentials..."
fi

$rootdir/bin/start-agent.sh

###################################
# Wait for the agent to boot
###################################

echo "Waiting for agent to start."
tail -f $tempfile | sed '/Output \[cloudwatchlogs\] buffer/ q'
containerId=$(docker ps -q)
echo "Agent started in container: $containerId."

###################################
# Run tests
###################################

cd $rootdir
tox -e integ
status_code=$?

###################################
# Cleanup
###################################

docker stop $containerId
rm -rf $tempfile
rm -rf ./.aws/credentials
rm -rf ./.aws/config

exit $status_code