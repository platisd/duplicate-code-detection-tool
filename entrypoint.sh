#!/bin/bash
set -eu

script_dir="$(dirname "$0")"
cd $script_dir

cat "$GITHUB_EVENT_PATH"

pull_request_id=$(cat "$GITHUB_EVENT_PATH" | jq '.issue.number')
branch_name="pull_request_branch"

eval git clone "https://${INPUT_GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" ${GITHUB_REPOSITORY}
cd $GITHUB_REPOSITORY
eval git config remote.origin.fetch +refs/heads/*:refs/remotes/origin/*
eval git fetch origin pull/$pull_request_id/head:$branch_name
eval git checkout $branch_name

latest_head=$(git rev-parse HEAD)

eval python3 /action/run_action.py --latest-head $latest_head
