#!/usr/bin/env bash
#
# usage:
# ./deploy.sh { LAMBDA_ARN } { region }

rootdir=$(git rev-parse --show-toplevel)

LIB_PATH=$rootdir
LAMBDA_EXAMPLE_PATH=$rootdir/examples/lambda
ZIP_NAME=function.zip
ZIP_PATH=$LAMBDA_EXAMPLE_PATH/$ZIP_NAME
AWS_LAMBDA_ARN=$1
REGION=$2

python3 -m venv venv
source venv/bin/activate
pip3 install $LIB_PATH
deactivate
cd venv/lib/python3.7/site-packages
zip -r9 $ZIP_PATH .
cd $LAMBDA_EXAMPLE_PATH
zip -g $ZIP_NAME function.py

# ###################################
# # Deploy Lambda
# ###################################

echo "Updating function code with archive at $ZIP_PATH.zip..."
aws lambda update-function-code \
    --function-name $AWS_LAMBDA_ARN \
    --region $REGION \
    --zip-file fileb://$ZIP_PATH

# ###################################
# # Cleanup temp files
# ###################################
rm $ZIP_PATH
