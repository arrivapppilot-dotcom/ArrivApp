# Create GitHub Personal Access Token

The backup script needs a GitHub Personal Access Token with `repo` scope to create releases.

## Step-by-Step

1. Go to: **https://github.com/settings/tokens**

2. Click **"Generate new token (classic)"**

3. Fill in the form:
   - **Token name**: `ArrivApp Backup Token`
   - **Expiration**: `No expiration` (or your preference)
   
4. **Select scopes** - check ONLY:
   - ✅ **repo** (this includes all repository permissions needed for releases)
     - ✔ repo:status
     - ✔ repo_deployment
     - ✔ public_repo
     - ✔ repo:invite
     - ✔ security_events

5. Click **"Generate token"**

6. **Copy the token** (it will only show once!)

7. Use it in terminal:
   ```bash
   export GITHUB_TOKEN="your_token_here"
   export GITHUB_REPO="arrivapppilot-dotcom/ArrivApp"
   cd backend
   python3 github_backup.py backup
   ```

## Why "repo" scope?

- Your previous token had "Contents" which only allows read/write of files
- Creating GitHub Releases requires full "repo" scope
- This is the minimal scope needed for the backup system

## Security Notes

- ✅ Token is only used to create releases in YOUR repository
- ✅ Token cannot delete/modify issues, PRs, or other content
- ✅ Store token securely (don't commit to git)
- ✅ Can revoke token anytime on GitHub settings page

