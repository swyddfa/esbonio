#!/bin/bash
# Make a dev release number based on the PR's issue number.

set -e

SRC=

case $1) in
    vscode)
        ;;
    python)
        SRC="lib/esbonio"
        ;;
    *)
        echo "Unkown component ${1}"
        exit 1
        ;;
esac

if [ -z "${SRC}" ];
    echo "SRC dir is not set!"
    exit 1
fi

cd ${SRC}

version=$(grep 'current_version' .bumpversion.cfg | sed 's/.*=\s\(.*\)/\1/')
build=$(echo $GITHUB_REF | sed -E 's/.*\/([0-9]+)\/.*/\1/')

echo "ref: ${GITHUB_REF}"
echo "Current Version: ${version}"
echo "Build number is ${build}"
echo

VERSION="${version}.dev${build}"
echo "Dev version number is: ${VERSION}"

python -m bumpversion --new-version "${VERSION}" dev