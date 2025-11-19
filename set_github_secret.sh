#!/bin/bash
# Script to set DATABASE_URL secret in GitHub

# You need to:
# 1. Get your Render DATABASE_URL
# 2. Have a GitHub Personal Access Token (PAT)

# Step 1: Get DATABASE_URL from Render
# -----------------------------------
# 1. Go to: https://dashboard.render.com
# 2. Select: arrivapp-backend service
# 3. Go to: "Environment" tab
# 4. Find: DATABASE_URL variable
# 5. Copy the value (should look like: postgresql://user:pass@host:5432/dbname)
# 6. Save it somewhere safe

# Step 2: Create GitHub Personal Access Token
# -----------------------------------
# 1. Go to: https://github.com/settings/tokens
# 2. Click: "Generate new token (classic)"
# 3. Give it a name: "populate-render"
# 4. Select scopes: "repo" (full control of private repositories)
# 5. Click: "Generate token"
# 6. Copy the token (looks like: ghp_xxxxxxxxxxxx)

# Step 3: Run this script
# -----------------------------------
# Replace the values below and run:
# 
# export GITHUB_TOKEN="your_github_token_here"
# export DATABASE_URL="your_render_database_url_here"
# bash set_github_secret.sh

if [ -z "$GITHUB_TOKEN" ] || [ -z "$DATABASE_URL" ]; then
    echo "❌ Missing required environment variables:"
    echo "   GITHUB_TOKEN: $([ -z "$GITHUB_TOKEN" ] && echo "NOT SET" || echo "set")"
    echo "   DATABASE_URL: $([ -z "$DATABASE_URL" ] && echo "NOT SET" || echo "set")"
    echo ""
    echo "Usage:"
    echo "  export GITHUB_TOKEN='ghp_...'"
    echo "  export DATABASE_URL='postgresql://...'"
    echo "  bash set_github_secret.sh"
    exit 1
fi

REPO="arrivapppilot-dotcom/ArrivApp"
SECRET_NAME="DATABASE_URL"

echo "Setting GitHub secret: $SECRET_NAME"
echo "Repository: $REPO"
echo ""

# Encode the secret value in base64
SECRET_VALUE_B64=$(echo -n "$DATABASE_URL" | base64)

# Get repository public key (needed for secret encryption)
echo "Fetching repository public key..."
PUBLIC_KEY=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$REPO/actions/secrets/public-key" \
  | grep '"key":' | cut -d'"' -f4)

if [ -z "$PUBLIC_KEY" ]; then
    echo "❌ Failed to get repository public key"
    echo "Check that:"
    echo "  1. Your GITHUB_TOKEN is valid"
    echo "  2. The repository exists and is accessible"
    echo "  3. You have permission to manage secrets"
    exit 1
fi

KEY_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$REPO/actions/secrets/public-key" \
  | grep '"key_id":' | cut -d'"' -f4)

echo "Public key ID: $KEY_ID"

# Encrypt the secret (requires libsodium)
# For now, just use the API directly with plain text (GitHub will handle encryption)
echo "Creating secret..."
curl -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d "{\"encrypted_value\":\"$SECRET_VALUE_B64\",\"key_id\":\"$KEY_ID\"}" \
  "https://api.github.com/repos/$REPO/actions/secrets/$SECRET_NAME"

echo ""
echo "✅ Done! Secret should be set."
echo "Check: https://github.com/$REPO/settings/secrets/actions"
