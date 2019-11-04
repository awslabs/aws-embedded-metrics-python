#!/usr/bin/env bash
#
# usage:
# ./start-endpoint.sh

rootdir=$(git rev-parse --show-toplevel)
pushd $rootdir/examples/ec2/metadata-endpoint
docker build -t ec2metadata:latest . 
docker run -d -p 3000:3000 --name "EC2Metadata" ec2metadata:latest
popd
