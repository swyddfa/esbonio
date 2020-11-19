#!/bin/bash
# Script to check if we should build a given component or not.

# File patterns to check for each component, if there's a match a build will be
# triggered
VSCODE="^code"
PYTHON="lib/esbonio"

# Determine which files have changed
files=$(git diff --name-only ${BASE}..HEAD -- )
echo -e "Files Changed:\n\n$files"

case $1 in
    vscode)
        PATTERN=${VSCODE}
        ;;
    python)
        PATTERN=${PYTHON}
        ;;
    *)
        echo "Unknown component ${1}"
        exit 1
        ;;
esac

changes=$(echo $files | grep -E "${PATTERN}")
echo
#echo $changes
#echo

if [ -z "$changes" ]; then
    echo "There is nothing to do."
else
    echo "Changes detected, doing build!"
    echo "::set-output name=build::true"
fi