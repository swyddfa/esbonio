#!/bin/bash
# Book keeping around making a release. This script will
#
# - Call bumpversion to generate a new version based on the changelog
# - Commit, tag and push the new version number.
# - Export the tag name and release date for use later on in the pipeline.
set -e

SRC=
TAG_PREFIX=
COMMIT_MSG=


COMPONENT=$1
case $1 in
    vscode)
        SRC="code"
        TAG_PREFIX="esbonio-vscode-extension-v"
        COMMIT_MSG="Esbonio VSCode Extension Release v"
        ;;
    extensions)
        SRC="lib/esbonio-extensions"
        TAG_PREFIX="esbonio-sphinx-extensions-v"
        COMMIT_MSG="Esbonio Sphinx Extensions Release v"
        ;;
    lsp)
        SRC="lib/esbonio"
        TAG_PREFIX="esbonio-language-server-v"
        COMMIT_MSG="Esbonio Language Server Release v"
        ;;
    *)
        echo "Unkown component ${1}"
        exit 1
        ;;
esac

if [ -z "${SRC}" ]; then
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

# Use the changelog to determine the type of release to make.
if [ ! -z "$(find changes -name '*.breaking.rst')" ]; then
    echo "Breaking changes found, doing major release!"
    KIND="major"
elif [ ! -z "$(find changes -name '*.feature.rst')" ]; then
    echo "New features found, doing minor release!"
    KIND="minor"
else
    echo "Doing patch release"
    KIND="patch"
fi

# Bump the version accordingly
python -m bumpversion ${KIND}
VERSION=$(grep 'current_version' .bumpversion.cfg | sed 's/.*=\s\(.*\)/\1/')

# If we're in a PR build, make a dev version number based on it.
if [[ "${GITHUB_REF}" == refs/pull/* ]]; then

    BUILD=$(echo $GITHUB_REF | sed -E 's/.*\/([0-9]+)\/.*/\1/')

    echo
    echo "ref: ${GITHUB_REF}"
    echo "Current Version: ${VERSION}"
    echo "Build number is ${BUILD}"
    echo

    # Annoying that this can't be the same...
    if [ "${COMPONENT}" = "vscode" ]; then
        VERSION="${VERSION}-dev${BUILD}"
    else
        VERSION="${VERSION}.dev${BUILD}"
    fi

    echo "Dev version number is: ${VERSION}"

    python -m bumpversion --allow-dirty --new-version "${VERSION}" dev

fi

TAG="${TAG_PREFIX}${VERSION}"
DATE=$(date +%Y-%m-%d)


# Only if we are on the release branch.
if [ "${GITHUB_REF}" = "refs/heads/release" ]; then

    # Make sure there's at least some changes...
    if [ -z "$(find changes -name '*.rst')" ]; then
        echo "There are no changes!"
        exit 1
    fi

    # Write the release notes for github
    python -m towncrier build --draft --version="${VERSION}" | \
        rst2html.py --template=changes/github-template.html > .changes.html

    # Write the release notes for the changelog
    python -m towncrier build --yes --version="${VERSION}"

    # Setup git, commit, tag and push all the changes.
    git config user.name github-actions
    git config user.email github-actions@github.com

    git commit -am "${COMMIT_MSG}${VERSION}"

    # Other stages may have run before this, make sure we have the latest
    git pull --rebase origin release
    git tag -a "${TAG}" -m "${COMMIT_MSG}${VERSION}"

    git push origin release
    git push origin --tags

    # Create a markdown copy of the Changelog, needed for the VSCode marketplace.
    pandoc CHANGES.rst -f rst -t gfm -o CHANGELOG.md

    # Export info that can be picked up in later steps.
    echo "VERSION=${VERSION}" >> $GITHUB_ENV
    echo "RELEASE_DATE=${DATE}" >> $GITHUB_ENV
    echo "RELEASE_TAG=${TAG}" >> $GITHUB_ENV
fi
