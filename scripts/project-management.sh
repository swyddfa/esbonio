#!/bin/bash

# This script is used to help automate project management in GitHub
# It expects to be called in a GitHub actions workflow with the following setup
#
# EVENT = github.event

# Configuration
#
# Here follows a bunch of magic numbers which correspond to IDs of the API
# objects we're insterested in.
LSP_PROJECT=11250171
LSP_BACKLOG=12653773


PREVIEW_HEADER="application/vnd.github.inertia-preview+json"


add_to_project () {

    issue_id=$1
    label_name=$2

    column_id=""

    case "${label_name}" in
        lsp)
            column_id=$LSP_BACKLOG
            ;;
        *)
            echo "Unknown label '${label_name}', doing nothing"
            return
            ;;
    esac

    echo "Adding issue '${issue_id}' to column '${column_id}'"
    curl -s -X POST "https://api.github.com/projects/columns/${column_id}/cards" \
         -H "Accept: ${PREVIEW_HEADER}" \
         -H "Authorization: Bearer ${GITHUB_TOKEN}" \
         -H "Content-Type: application/json" \
         -d "{\"content_id\": ${issue_id}, \"content_type\": \"Issue\"}"
}


#
# Script start.
#


if [ -z "${GITHUB_TOKEN}" ]; then
   echo "Github token is not set."
   exit 1
fi

action=$(echo "${EVENT}" | jq -r .action)
label_name=$(echo "${EVENT}" | jq -r .label.name)
issue=$(echo "${EVENT}" | jq -r .issue.id )

echo "Action:   ${action}"
echo "Label:    ${label_name}"
echo "Issue Id: ${issue}"

case "$action" in
    labeled)
        add_to_project "${issue}" "${label_name}"
    ;;
    *)
        echo "Unknown action '${action}', doing nothing"
esac
