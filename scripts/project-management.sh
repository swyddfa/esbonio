#!/bin/bash

# This script is used to help automate project management in GitHub
# It expects to be called in a GitHub actions workflow with the following setup
#
# EVENT = github.event
# GITHUB_TOKEN = secrets.GITHUB_TOKEN

# Configuration
#
# Here follows a bunch of magic numbers which correspond to IDs of the API
# objects we're insterested in.
LSP_PROJECT=11250171
LSP_BACKLOG=12653773

VSCODE_PROJECT=11250281
VSCODE_BACKLOG=12653879

PREVIEW_HEADER="application/vnd.github.inertia-preview+json"


add_to_project () {

    issue_id=$1
    label_name=$2

    column_id=""

    case "${label_name}" in
        lsp)
            column_id=$LSP_BACKLOG
            ;;
        vscode)
            column_id=$VSCODE_BACKLOG
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


remove_from_project () {

    issue_number=$1
    label_name=$2

    case "${label_name}" in
        lsp)
            column_id=$LSP_BACKLOG
            ;;
        vscode)
            column_id=$VSCODE_BACKLOG
            ;;
        *)
            echo "Unknown label '${label_name}', doing nothing"
            return
            ;;
    esac

    # Need to look to see which card corresponds to the issue.
    echo "Looking for issue in column '${column_id}'"
    card_id=$(curl -s -X GET "https://api.github.com/projects/columns/${column_id}/cards" \
         -H "Accept: ${PREVIEW_HEADER}" \
         -H "Authorization: Bearer ${GITHUB_TOKEN}" | jq --arg issue "${issue_number}" -r '.[] | select(.content_url | test(\".*/$issue\") | .id')

    if [ -z "${card_id}" ]; then
        echo "Couldn't find card for issue '${issue_number}', doing nothing"
        return
    fi

    echo "Removing card '${card_id}' from column '${column_id}'"
    curl -s -X DELETE "https://api.github.com/projects/columns/cards/${card_id}" \
         -H "Accept: ${PREVIEW_HEADER}" \
         -H "Authorization: Bearer ${GITHUB_TOKEN}"
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
issue_number=$(echo "${EVENT}" | jq -r .issue.number)

echo
echo "Action:       ${action}"
echo "Label:        ${label_name}"
echo "Issue Id:     ${issue}"
echo "Issue Number: ${issue_number}"
echo

case "$action" in
    labeled)
        add_to_project "${issue}" "${label_name}"
        ;;
    unlabeled)
        remove_from_project "${issue_number}" "${label_name}"
        ;;
    *)
        echo "Unknown action '${action}', doing nothing"
esac
