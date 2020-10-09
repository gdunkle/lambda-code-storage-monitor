#!/bin/bash
export ACCOUNT_NAME=${ACCOUNT_NAME:=awsgalen-ct-dev-001}
export SOLUTION_NAME=lambda-code-storage-monitor
export DIST_OUTPUT_BUCKET=${DIST_OUTPUT_BUCKET:=awsgalen-solutions}
export VERSION=1.0.0
export AWS_REGION=${AWS_REGION:=us-east-2}
echo $SOLUTION_NAME 
echo $DIST_OUTPUT_BUCKET
echo $VERSION
echo $AWS_REGION

./build-s3-dist.sh $DIST_OUTPUT_BUCKET $SOLUTION_NAME $VERSION
aws s3 cp ./regional-s3-assets/ s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control
parameter_file=./parameters/$ACCOUNT_NAME-$AWS_REGION.json
echo "jq -r '.[] | [.ParameterKey, .ParameterValue] | join(\"=\")' $parameter_file"
parameter_overrides=$(jq -r '.[] | [.ParameterKey, .ParameterValue] | join("=")' $parameter_file)
echo $parameter_overrides
echo "Deploying stack $SOLUTION_NAME"
echo "aws cloudformation deploy  --stack-name $SOLUTION_NAME --s3-bucket $DIST_OUTPUT_BUCKET-$AWS_REGION --s3-prefix $SOLUTION_NAME/$VERSION --template-file ./global-s3-assets/solution.template  --capabilities CAPABILITY_IAM"
aws cloudformation deploy --region $AWS_REGION --parameter-overrides $parameter_overrides   --stack-name $SOLUTION_NAME --s3-bucket $DIST_OUTPUT_BUCKET-$AWS_REGION --s3-prefix $SOLUTION_NAME/$VERSION --template-file ./global-s3-assets/solution.template  --capabilities CAPABILITY_IAM
    

