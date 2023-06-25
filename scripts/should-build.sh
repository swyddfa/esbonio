#!/bin/bash
# Script to check if we should build a given component or not.

# File patterns to check for each component, if there's a match a build will be
# triggered
DOCS="^docs|^lib/.*.py"
LSP="^lib/esbonio/"
EXTENSIONS="^lib/esbonio-extensions/"
VSCODE="^code"

# Determine which files have changed
git diff --name-only ${BASE}..HEAD -- >> changes
echo -e "Files Changed:\n"
cat changes

case $1 in
    docs)
        PATTERN=${DOCS}
        ;;
    extensions)
        PATTERN=${EXTENSIONS}
        ;;
    lsp)
        PATTERN=${LSP}
        ;;
    vscode)
        PATTERN=${VSCODE}
        ;;
    *)
        echo "Unknown component ${1}"
        exit 1
        ;;
esac

changes=$(grep -E "${PATTERN}" changes)
echo

rm changes

if [ -z "$changes" ]; then
    echo "There is nothing to do."
else
    echo "Changes detected, doing build!"
    echo "build=true" >> $GITHUB_OUTPUT
fi
