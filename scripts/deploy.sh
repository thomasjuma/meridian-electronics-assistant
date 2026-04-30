#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}          # dev | test | prod
PROJECT_NAME=${2:-meridian}
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
LAMBDA_PACKAGE="$BACKEND_DIR/lambda-deployment.zip"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "🚀 Deploying ${PROJECT_NAME} to ${ENVIRONMENT}..."

case "$ENVIRONMENT" in
  dev|test|prod) ;;
  *)
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "   Allowed values: dev, test, prod"
    exit 1
    ;;
esac

# 1. Build backend Lambda package
cd "$ROOT_DIR"
echo "📦 Preparing backend package..."
if [ -f "$BACKEND_DIR/deploy.py" ]; then
  (cd "$BACKEND_DIR" && uv run deploy.py)
else
  echo "⚠️ backend/deploy.py not found. Creating lambda package from source files..."
  rm -f "$LAMBDA_PACKAGE"
  (
    cd "$BACKEND_DIR"
    zip -rq "$LAMBDA_PACKAGE" app main.py pyproject.toml uv.lock \
      -x "*/__pycache__/*" "*.pyc" ".venv/*" "test.db"
  )
fi

# 2. Terraform workspace & apply
cd "$ROOT_DIR/terraform"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${DEFAULT_AWS_REGION:-eu-west-1}
TF_STATE_BUCKET="meridian-terraform-state-${AWS_ACCOUNT_ID}"
TF_LOCK_TABLE="meridian-terraform-locks"

echo "🧱 Ensuring Terraform backend resources exist..."
if ! aws s3api head-bucket --bucket "$TF_STATE_BUCKET" 2>/dev/null; then
  echo "  Creating S3 state bucket: $TF_STATE_BUCKET"
  if [ "$AWS_REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$TF_STATE_BUCKET" >/dev/null
  else
    aws s3api create-bucket \
      --bucket "$TF_STATE_BUCKET" \
      --region "$AWS_REGION" \
      --create-bucket-configuration "LocationConstraint=$AWS_REGION" >/dev/null
  fi

  aws s3api put-bucket-versioning \
    --bucket "$TF_STATE_BUCKET" \
    --versioning-configuration Status=Enabled >/dev/null
  aws s3api put-bucket-encryption \
    --bucket "$TF_STATE_BUCKET" \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' >/dev/null
fi

if ! aws dynamodb describe-table --table-name "$TF_LOCK_TABLE" --region "$AWS_REGION" >/dev/null 2>&1; then
  echo "  Creating DynamoDB lock table: $TF_LOCK_TABLE"
  aws dynamodb create-table \
    --table-name "$TF_LOCK_TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "$AWS_REGION" >/dev/null
fi

terraform init -input=false \
  -backend-config="bucket=${TF_STATE_BUCKET}" \
  -backend-config="key=${ENVIRONMENT}/terraform.tfstate" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${TF_LOCK_TABLE}" \
  -backend-config="encrypt=true"

if ! terraform workspace list | grep -q "$ENVIRONMENT"; then
  terraform workspace new "$ENVIRONMENT"
else
  terraform workspace select "$ENVIRONMENT"
fi

# Use prod.tfvars for production environment
if [ "$ENVIRONMENT" = "prod" ]; then
  TF_APPLY_CMD=(terraform apply -var-file=prod.tfvars -var="project_name=$PROJECT_NAME" -var="environment=$ENVIRONMENT" -auto-approve)
else
  TF_APPLY_CMD=(terraform apply -var="project_name=$PROJECT_NAME" -var="environment=$ENVIRONMENT" -auto-approve)
fi

echo "🎯 Applying Terraform..."
"${TF_APPLY_CMD[@]}"

API_URL=$(terraform output -raw api_gateway_url)
FRONTEND_BUCKET=$(terraform output -raw s3_frontend_bucket)
CUSTOM_URL=$(terraform output -raw custom_domain_url 2>/dev/null || true)

# 3. Build + deploy frontend
cd "$FRONTEND_DIR"

# Create environment files with deployed API URL
echo "📝 Setting API URL for production..."
API_BASE_URL="${API_URL%/}/api"
echo "NG_APP_API_BASE_URL=${API_BASE_URL}" > .env.production
echo "NG_APP_API_BASE_URL=${API_BASE_URL}" > .env

npm install
NG_APP_API_BASE_URL="${API_BASE_URL}" npm run build
aws s3 sync ./dist/meridian-chat/browser "s3://$FRONTEND_BUCKET/" --delete
cd ..

# 4. Final messages
echo -e "\n✅ Deployment complete!"
echo "🌐 CloudFront URL : $(terraform -chdir=terraform output -raw cloudfront_url)"
if [ -n "$CUSTOM_URL" ]; then
  echo "🔗 Custom domain  : $CUSTOM_URL"
fi
echo "📡 API Gateway    : $API_URL"