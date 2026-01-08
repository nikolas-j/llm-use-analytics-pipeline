set -euo pipefail

# ====== EDIT THESE ======
REGION="eu-north-1"
CLUSTER="my-cluster"
TASK_DEF="my-ecs-task:1"
CONTAINER_NAME="container-name"

SUBNET_ID="subnet-XXXXXXXXXX"
SECURITY_GROUP_ID="sg-XXXXXXXXXXXXXXX"
ASSIGN_PUBLIC_IP="ENABLED"   # use ENABLED for easiest manual runs

AWS_REGION_ENV="eu-north-1"  # the Bedrock region your code uses (must match your model ARN)
LLM_CLASSIFICATION="true"
DATE=2026-01-03 # Test date
# ========================

echo "Running ECS task..."
aws ecs run-task \
  --region "$REGION" \
  --cluster "$CLUSTER" \
  --launch-type FARGATE \
  --task-definition "$TASK_DEF" \
  --count 1 \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=$ASSIGN_PUBLIC_IP}" \
  --query "tasks[0].taskArn" \
  --output text
