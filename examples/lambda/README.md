# Lambda Function Example

1. Edit the function.py example as desired
2. Create a lambda function
3. Run the deploy script providing the ARN and region

```sh
./deploy.sh arn:aws:lambda:<REGION>:<ACCOUNT>:function:<FUNCTION_NAME> <REGION>
# example:
# ./deploy.sh arn:aws:lambda:us-east-1:123456789012:function:MyFunction us-east-1
```
