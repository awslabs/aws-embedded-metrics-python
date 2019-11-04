#!/usr/bin/env bash
#
# usage:
#   export AWS_ACCESS_KEY_ID=
#   export AWS_SECRET_ACCESS_KEY=
#   export AWS_REGION=us-west-2
#   ./run-example.sh

rootdir=$(git rev-parse --show-toplevel)
tempfile="$rootdir/tests/integ/agent/.temp"

export AWS_EMF_AGENT_ENDPOINT=udp://0.0.0.0:25888
export AWS_EMF_EC2_METADATA_ENDPOINT=http://localhost:3000/ec2-metadata

###################################
# Install the library
###################################

python3 -m venv venv
source venv/bin/activate
pip3 install $rootdir

###################################
# Start the metadata endpoint
###################################

$rootdir/examples/ec2/metadata-endpoint/start-endpoint.sh
echo "Waiting for endpoint to start."
sleep 2
ec2ContainerId=$(docker ps -q --filter name=EC2Metadata)
echo "EC2 Metadata Container started in: $ec2ContainerId."

###################################
# Configure and start the agent
###################################

$rootdir/bin/start-agent.sh

###################################
# Wait for the agent to boot
###################################

echo "Waiting for agent to start."
tail -f $tempfile | sed '/Output \[cloudwatchlogs\] buffer/ q'
agentContainerId=$(docker ps -q --filter name=CWAgent)
echo "Agent started in container: $agentContainerId."

###################################
# Start the example app
###################################
cd $rootdir/examples/ec2
python3 app.py 

###################################
# Cleanup
###################################

docker stop $agentContainerId
docker rm $agentContainerId

docker stop $ec2ContainerId
docker rm $ec2ContainerId

rm -rf $tempfile
rm -rf ./.aws/credentials
rm -rf ./.aws/config

deactivate