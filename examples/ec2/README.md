# EC2 Example

## Running Locally

This example provides the tools required to emulate a remote EC2 deployment.
The only pre-requisites are that your machine needs to have Docker installed
and you need to have valid AWS credentials.

This example:

- Starts a local EC2 metadata endpoint on 3000/tcp. The library uses this to auto-configure itself
- Starts the CloudWatch Agent
- Sets up a virtual environment, installs the library and starts the python app.py script

Insert your credentials into the environment variables below and run the script:

```
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
export AWS_REGION=

./run-example.sh
```
