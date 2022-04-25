#!/bin/bash
set -eu

script_dir="$(dirname "$0")"
cd $script_dir

pull_request_id=$(cat "$GITHUB_EVENT_PATH" | jq 'if (.issue.number != null) then .issue.number else .number end')
branch_name="pull_request_branch"

if [ $pull_request_id == "null" ]; then
  echo "Could not find a pull request ID. Is this a pull request?"
  exit 1
fi

maintainer=${GITHUB_REPOSITORY%/*}
eval git clone "https://${maintainer}:${INPUT_GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" ${GITHUB_REPOSITORY}
cd $GITHUB_REPOSITORY
eval git config remote.origin.fetch +refs/heads/*:refs/remotes/origin/*
eval git fetch origin pull/$pull_request_id/head:$branch_name
eval git checkout $branch_name

latest_head=$(git rev-parse HEAD)

eval python3 /action/run_action.py --latest-head $latest_head --pull-request-id $pull_request_id

echo "::set-output name=markdown::strawberry"
