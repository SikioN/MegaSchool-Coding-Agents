#!/bin/bash
set -e

# Configuration
SERVICE_NAME="megaschool-agent"
# --- ВВЕДИТЕ ID ВАШЕГО РЕЕСТРА НИЖЕ ---
# Пример: REGISTRY_ID="crp1234567890abcdef"
REGISTRY_ID="crpc4h1md9d242gbkd12" 

if [ -z "$REGISTRY_ID" ]; then
  echo "❌ Error: Please open deploy_yandex.sh and set REGISTRY_ID!"
  echo "   You can create one with: 'yc container registry create --name agent-registry'"
  exit 1
fi

IMAGE_URI="cr.yandex/$REGISTRY_ID/$SERVICE_NAME:latest"

echo "🚀 Starting Deployment to Yandex Cloud Serverless..."

# 1. Build Docker Image
echo "🔨 Building Docker image (linux/amd64)..."
docker build --platform linux/amd64 -t $IMAGE_URI .

# 2. Push to Registry
echo "🔐 Logging in to Yandex Registry (isolated environment)..."
export DOCKER_CONFIG=$(mktemp -d)
echo $(yc iam create-token) | docker login --username iam --password-stdin cr.yandex

echo "📤 Pushing to Yandex Container Registry..."
docker push $IMAGE_URI

# 3. Deploy Container
echo "☁️  Updating Serverless Container..."

# Create Service Account if missing
if ! yc iam service-account get agent-sa > /dev/null 2>&1; then
  echo "👤 Creating Service Account 'agent-sa'..."
  yc iam service-account create --name agent-sa
fi
SA_ID=$(yc iam service-account get agent-sa --format json | jq -r .id)

# Grant 'container-registry.images.puller' role to SA
echo "👮 Granting puller role to Service Account..."
FOLDER_ID=$(yc config get folder-id)
yc resource-manager folder add-access-binding --id $FOLDER_ID --role container-registry.images.puller --subject serviceAccount:$SA_ID > /dev/null

# 3.1 Setup Object Storage (S3) for Logs
BUCKET_NAME="megaschool-logs-$(echo $REGISTRY_ID | cut -c1-6)" # Unique-ish bucket
echo "📦 Setting up S3 Bucket: $BUCKET_NAME..."

if ! yc storage bucket get $BUCKET_NAME > /dev/null 2>&1; then
  echo "🆕 Creating Bucket..."
  yc storage bucket create --name $BUCKET_NAME
else
  echo "✅ Bucket exists."
fi

# 3.2 Grant Storage Role to SA
echo "👮 Granting storage.editor role to Service Account..."
yc resource-manager folder add-access-binding --id $FOLDER_ID --role storage.editor --subject serviceAccount:$SA_ID > /dev/null

# Make container public (allow unauthenticated invoke)
echo "🌍 Making container public..."
if ! yc serverless container list-access-bindings --name $SERVICE_NAME | grep -q "system:allUsers"; then
   yc serverless container add-access-binding --name $SERVICE_NAME --role serverless.containers.invoker --subject system:allUsers
fi

# Check if container exists, create if not
if ! yc serverless container get $SERVICE_NAME > /dev/null 2>&1; then
  echo "🆕 Creating Serverless Container '$SERVICE_NAME'..."
  yc serverless container create --name $SERVICE_NAME
fi

# Load env vars for secrets
if [ -f .env ]; then
  echo "🔑 Loading secrets from .env..."
  set -a
  source .env
  set +a
else
  echo "⚠️  .env file not found! Secrets might be missing."
fi

# Deploy
yc serverless container revision deploy \
  --container-name $SERVICE_NAME \
  --image $IMAGE_URI \
  --cores 1 \
  --memory 512M \
  --concurrency 1 \
  --execution-timeout 30s \
  --service-account-id $SA_ID \
  --environment GITHUB_APP_ID="$GITHUB_APP_ID",GITHUB_WEBHOOK_SECRET="$GITHUB_WEBHOOK_SECRET",GITHUB_PRIVATE_KEY="$GITHUB_PRIVATE_KEY",LLM_API_KEY="$LLM_API_KEY",YC_FOLDER_ID="$YC_FOLDER_ID",DASHBOARD_API_URL="$DASHBOARD_API_URL",S3_BUCKET_NAME="$BUCKET_NAME"

echo "✅ Deployment Complete!"
echo "   Go to Yandex Console -> Serverless Containers to get your new URL."
