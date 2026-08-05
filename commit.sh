#!/usr/bin/env bash
cd "$(dirname "$0")"

read -p "commit message: " msg

if [ -z "$msg" ]; then
    echo "commit message cannot be empty (err)"
    exit 1
fi

git add .
git commit -m "$msg"

if [ $? -ne 0 ]; then
    echo "commit failed, nothing pushed"
    exit 1
fi

git push

if [ $? -ne 0 ]; then
    echo "push failed"
    exit 1
fi

echo "done"