#!/bin/bash
set -e

# Configuration
SERVICE_NAME="megaschool-agent"
# --- ВВЕДИТЕ ID ВАШЕГО РЕЕСТРА НИЖЕ ---
# Пример: REGISTRY_ID="crp1234567890abcdef"
REGISTRY_ID="" 

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
echo "📤 Pushing to Yandex Container Registry..."
docker push $IMAGE_URI

# 3. Deploy Container
echo "☁️  Updating Serverless Container..."

# Load env vars for secrets
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "⚠️  .env file not found! Secrets might be missing."
fi

# We use the env vars from current shell (exported above)
yc serverless container revision deploy \
  --container-name $SERVICE_NAME \
  --image $IMAGE_URI \
  --cores 1 \
  --memory 512M \
  --concurrency 1 \
  --execution-timeout 30s \
  --service-account-id $(yc iam service-account get agent-sa --format json | jq -r .id || echo "") \
  --environment GITHUB_APP_ID="$GITHUB_APP_ID",GITHUB_WEBHOOK_SECRET="$GITHUB_WEBHOOK_SECRET",GITHUB_PRIVATE_KEY="$GITHUB_PRIVATE_KEY",LLM_API_KEY="$LLM_API_KEY",YC_FOLDER_ID="$YC_FOLDER_ID"

echo "✅ Deployment Complete!"
echo "   Go to Yandex Console -> Serverless Containers to get your new URL."
