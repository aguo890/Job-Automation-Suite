#!/bin/bash
set -e # Exit on any error

# [AI AGENT CONTEXT]: We operate entirely in /tmp to prevent changing 
# the Git branch of the active, running application.
BACKUP_FILE="/tmp/job_suite_backup.tar.gz"
TMP_REPO_DIR="/tmp/dr_backup_repo"

# Ensure we are in a known state (app root) if possible, 
# but we'll use absolute paths for the archive to be safest.
APP_ROOT="/app"
DATA_DIR="$APP_ROOT/job-scraping-app/data"
CV_DIR="$APP_ROOT/generated_cvs"

echo "📦 Archiving state data..."
# Archive the specific state directories. 
# We use -C to change directory so the paths in the tar are relative to APP_ROOT.
tar -czf $BACKUP_FILE -C $APP_ROOT job-scraping-app/data generated_cvs

echo "🔧 Preparing isolated Git environment..."
rm -rf $TMP_REPO_DIR
mkdir -p $TMP_REPO_DIR
cd $TMP_REPO_DIR

# Initialize empty repo and set bot identity
git init
git config user.name "Automated DR Bot"
git config user.email "dr-bot@job-suite.local"

# Add the remote using the token for authentication
# GITHUB_TOKEN and GITHUB_REPOSITORY must be set in the environment
if [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_REPOSITORY" ]; then
    echo "❌ Error: GITHUB_TOKEN or GITHUB_REPOSITORY is not set."
    exit 1
fi

git remote add origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"

echo "💾 Committing backup..."
cp $BACKUP_FILE .
git add job_suite_backup.tar.gz
git commit -m "Automated DR Backup: $(date)"

echo "🚀 Force pushing to dr-backups branch..."
# Push this single commit directly to the dr-backups branch, overwriting history
# Note: We push the local 'master' (default init branch) to remote 'dr-backups'
git push origin master:dr-backups --force

echo "🧹 Cleaning up..."
rm -rf $TMP_REPO_DIR $BACKUP_FILE

echo "✅ Backup completed successfully!"
