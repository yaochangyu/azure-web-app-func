#!/bin/bash

# 建立空 commit 以觸發 GitHub Actions 部署

git commit --allow-empty -m "chore: trigger deployment - $(date '+%Y-%m-%d %H:%M:%S')"
