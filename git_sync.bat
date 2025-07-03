@echo off
echo ?? Pulling latest changes...
git pull --rebase origin main

echo ? Staging all changes...
git add .

echo ?? Committing...
git commit -m "Update"

echo ?? Pushing to origin/main...
git push

pause
