#!/bin/bash
# Book keeping around making a release. This script will
#
# - Call bumpversion to generate a new version based on the commit message
# - Commit, tag and push the new version number.
# - Export the tag name and release date for use later on in the pipeline.
set -e

SRC=
TAG_PREFIX=
COMMIT_MSG=

case $1 in
    vscode)
        ;;
    python)
        SRC="lib/esbonio"
        TAG_PREFIX="esbonio-lib-v"
        COMMIT_MSG="Esbonio Lib Release v"
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

if [ -z "${TAG_PREFIX}" ]; then
    echo "TAG_PREFIX is not set!"
    exit 1
fi

if [ -z "${COMMIT_MSG}" ]; then
    echo "COMMIT_MSG is not set!"
    exit 1
fi

cd ${SRC}

message=$(git log HEAD --pretty=format:'%s' | head -n 1 | tr '[:upper:]' '[:lower:]')
echo "Commit message: ${message}"

case $message in
    major*)
        KIND="major";;
    minor*)
        KIND="minor";;
    *)
        KIND="patch";;
esac

python -m bumpversion ${KIND}
VERSION=$(grep 'current_version' .bumpversion.cfg | sed 's/.*=\s\(.*\)/\1/')

git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git config user.name "github-actions[bot]"

TAG="${TAG_PREFIX}${VERSION}"
DATE=$(date +%Y-%m-%d)

git commit -am "${COMMIT_MSG}${VERSION}"
git tag -a "${TAG}" -m "${COMMIT_MSG}${VERSION}"

git push origin release
git push origin --tags

# Export info that can be picked up in later steps.
echo "::set-output name=VERSION::${VERSION}"
echo "::set-output name=TAG::${TAG}"
echo "::set-output name=DATE::${DATE}"