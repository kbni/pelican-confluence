#!/usr/bin/env bash

set -e                  # exit script if errors are encountered
cd "$(dirname "$0")"   # cd to where this script lives

# Publish using rclone
rclone -v sync ./data/output kbni-net-au:kbni.net.au

