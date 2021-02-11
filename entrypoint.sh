#!/bin/bash
set -eu

script_dir="$(dirname "$0")"
cd $script_dir

eval git clone "https://${INPUT_GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" ${GITHUB_REPOSITORY}
cd $GITHUB_REPOSITORY
eval git config remote.origin.fetch +refs/heads/*:refs/remotes/origin/*
eval git fetch --all
eval git checkout ${GITHUB_HEAD_REF:-$(basename ${GITHUB_REF})}

eval python3 /action/run.py
