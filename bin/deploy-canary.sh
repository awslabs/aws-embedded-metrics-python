#!/usr/bin/env bash

rootdir=$(git rev-parse --show-toplevel)
rootdir=${rootdir:-$(pwd)} # in case we are not in a git repository (Code Pipelines)
source $rootdir/bin/utils.sh

LIB_PATH=$rootdir
CANARY_PATH=$LIB_PATH/tests/canary/agent
ACCOUNT_ID=863722843142
REGION=us-west-2
IMAGE_NAME=emf-python-canary
ECS_CLUSTER_NAME=emf-canary
ECS_TASK_FAMILY=emf-python-canary
ECS_SERVICE_NAME=emf-python-canary
ECR_REMOTE=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$IMAGE_NAME

pushd $CANARY_PATH
echo 'INSTALLING LOCAL PROJECT'
python3 -m venv venv
source venv/bin/activate
pip3 install $rootdir
pip3 install psutil
pip3 install getversion

echo 'BUILDING THE EXAMPLE DOCKER IMAGE'
`aws ecr get-login --no-include-email --region $REGION`
docker build . -t $IMAGE_NAME:latest 
check_exit

echo 'PUSHING THE EXAMPLE DOCKER IMAGE TO ECR'
imageid=$(docker images -q $IMAGE_NAME:latest)
docker tag $imageid $ECR_REMOTE
docker push $ECR_REMOTE
check_exit

echo 'UPDATING THE ECS SERVICE'
aws ecs update-service \
  --region $REGION \
  --cluster $ECS_CLUSTER_NAME \
  --service $ECS_SERVICE_NAME \
  --force-new-deployment \
  --task-definition $(aws ecs register-task-definition \
                        --network-mode bridge \
                        --requires-compatibilities EC2 \
                        --task-role arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole \
                        --execution-role-arn "arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole" \
                        --region $REGION \
                        --memory 256 \
                        --cpu '0.5 vcpu' \
                        --family $ECS_TASK_FAMILY \
                        --container-definitions "$(cat container-definitions.json)" \
                    | jq --raw-output '.taskDefinition.taskDefinitionArn' | awk -F '/' '{ print $2 }')

popd

###################################
# Cleanup
###################################
deactivate