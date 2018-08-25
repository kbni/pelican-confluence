#!/usr/bin/env bash

set -e                  # exit script if errors are encountered
cd "$(dirname "$0")"   # cd to where this script lives

# Retreieve all our Confluence content and export it for processing by Pelican
python -m confluence2pelican -es

# Run pelican to process the exported output and pass any arguments here
pelican -r -s data/pelicanconf.py --ignore-cache "$@"

