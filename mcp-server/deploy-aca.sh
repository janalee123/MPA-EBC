#!/bin/bash
# MPA Oceans-X MCP Server - Azure Container Apps Deployment Script
# 
# Prerequisites:
#   - Azure CLI installed and logged in (az login)
#   - Contributor or Owner role on the target resource group
#   - Docker (optional - for local build before push)
#
# Usage:
#   chmod +x deploy-aca.sh
#   ./deploy-aca.sh

set -e

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-agentic-ai-demo-RG}"
LOCATION="${LOCATION:-eastus}"
ACR_NAME="${ACR_NAME:-oceanxacr$RANDOM}"
ENVIRONMENT_NAME="${ENVIRONMENT_NAME:-ocean-x-env}"
APP_NAME="${APP_NAME:-ocean-x-mcp}"
IMAGE_TAG="${IMAGE_TAG:-1.0.0}"
TARGET_PORT="${TARGET_PORT:-8000}"

echo "=============================================="
echo "MPA Oceans-X MCP Server - ACA Deployment"
echo "=============================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "ACR Name: $ACR_NAME"
echo "Environment: $ENVIRONMENT_NAME"
echo "App Name: $APP_NAME"
echo "Image Tag: $IMAGE_TAG"
echo "=============================================="

# Step 1: Create ACR if it doesn't exist
echo ""
echo "Step 1: Creating Azure Container Registry..."
if az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "ACR $ACR_NAME already exists"
else
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Basic \
        --admin-enabled true \
        --location $LOCATION
    echo "ACR $ACR_NAME created"
fi

ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)
echo "ACR Login Server: $ACR_LOGIN_SERVER"

# Step 2: Build and push image to ACR
echo ""
echo "Step 2: Building and pushing Docker image..."
cd "$(dirname "$0")"

az acr build \
    --registry $ACR_NAME \
    --image jana/ocean-x-mcp-demo:$IMAGE_TAG \
    --file Dockerfile \
    .

echo "Image pushed: $ACR_LOGIN_SERVER/jana/ocean-x-mcp-demo:$IMAGE_TAG"

# Step 3: Create Container Apps Environment if it doesn't exist
echo ""
echo "Step 3: Creating Container Apps Environment..."
if az containerapp env show --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "Environment $ENVIRONMENT_NAME already exists"
else
    az containerapp env create \
        --name $ENVIRONMENT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION
    echo "Environment $ENVIRONMENT_NAME created"
fi

# Step 4: Deploy Container App
echo ""
echo "Step 4: Deploying Container App..."

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

if az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "Updating existing app $APP_NAME..."
    az containerapp update \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image "$ACR_LOGIN_SERVER/jana/ocean-x-mcp-demo:$IMAGE_TAG"
else
    echo "Creating new app $APP_NAME..."
    az containerapp create \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $ENVIRONMENT_NAME \
        --image "$ACR_LOGIN_SERVER/jana/ocean-x-mcp-demo:$IMAGE_TAG" \
        --registry-server $ACR_LOGIN_SERVER \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --target-port $TARGET_PORT \
        --ingress external \
        --min-replicas 1 \
        --max-replicas 3 \
        --cpu 0.5 \
        --memory 1Gi
fi

# Step 5: Get the FQDN
echo ""
echo "Step 5: Getting deployment URL..."
FQDN=$(az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "=============================================="
echo "Deployment Complete!"
echo "=============================================="
echo "App URL: https://$FQDN"
echo "MCP Endpoint: https://$FQDN/mcp"
echo ""
echo "Test with:"
echo "  curl -X POST https://$FQDN/mcp \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"capabilities\":{}},\"id\":1}'"
echo "=============================================="
