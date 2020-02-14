#!/usr/bin/env bash
#
# Author: Trevor SANDY
# Last Update February 12, 2020
#
# Adapted from original script by Stefan Buck
# License: MIT
#
# Script to upload a release asset using the GitHub API v3.
#
# Example:
#
# ./upload-github-release-asset.sh
#
# This script accepts the following parameters:
# TAG          - Release tag
# OWNER        - Repository owner
# REPO_NAME    - Repository 
# REPO_PATH    - Full path to the repository
# ASSET_NAME   - File name
# API_TOKEN    - User GitHub Token (Use a local file containing your token)
#

SCRIPT_NAME=$0
SCRIPT_ARGS=$*
HOME_DIR=$PWD

echo && echo $SCRIPT_NAME && echo

# Check for archive dependencies
echo
set -e
echo -n "Checking dependencies... "
for name in zip jq xargs
do
  [[ $(which $name 2>/dev/null) ]] || { echo -en "\n$name needs to be installed. Use 'sudo apt-get install $name'";deps=1; }
done
[[ $deps -ne 1 ]] && echo "OK" || { echo -en "\nInstall the above and rerun this script\n";exit 1; }

# Validate settings.
[ "$TRACE" ] && set -x

CONFIG=$@

for line in $CONFIG; do
  eval "$line"
done

# Arguments
GH_TAG=${TAG:-v1.0.0}
GH_OWNER=${OWNER:-trevorsandy}
GH_REPO_NAME=${REPO_NAME:-blenderldrawrender}
GH_REPO_PATH=${REPO_PATH:-/home/$GH_OWNER/projects/$GH_REPO_NAME}
GH_ASSET_NAME=${ASSET_NAME:-LDrawBlenderRenderAddons.zip}
GH_API_TOKEN=${API_TOKEN:-}

cd $GH_REPO_PATH

# Define variables.
GH_API="https://api.github.com"
GH_REPO="$GH_API/repos/$GH_OWNER/$GH_REPO_NAME"
GH_TAGS="$GH_REPO/releases/tags/$GH_TAG"
GH_AUTH="Authorization: token $GH_API_TOKEN"
WGET_ARGS="--content-disposition --auth-no-challenge --no-cookie"
CURL_ARGS="-LJO#"

function display_arguments
{
    echo
    echo "--Command Options:"
    echo "--GH_TAG.........$GH_TAG"
    echo "--GH_OWNER.......$GH_OWNER"    
    echo "--GH_REPO_NAME...$GH_REPO_NAME"
    echo "--GH_REPO_PATH...$GH_REPO_PATH"
	echo "--GH_ASSET_NAME..$GH_ASSET_NAME"
    echo "--GH_API.........$GH_API"
    echo "--GH_REPO........$GH_REPO"
    echo "--GH_TAGS........$GH_TAGS"
    echo 
}

ME="$(basename "$(test -L "$0" && readlink "$0" || echo "$0")")"
CWD=`pwd`
f="${CWD}/$ME"
ext=".log"
if [[ -e "$f$ext" ]] ; then
    i=1
    f="${f%.*}";
    while [[ -e "${f}_${i}${ext}" ]]; do
      let i++
    done
    f="${f}_${i}${ext}"
    else
    f="${f}${ext}"
fi
# output log file
LOG="$f"
exec > >(tee -a ${LOG} )
exec 2> >(tee -a ${LOG} >&2)

# Show options
display_arguments

# Confirmation
sleep 1s && read -p "  Are you sure (y/n)? " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
  [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1 # handle exits from shell or function but don't exit interactive shell
fi

# Get API Token from file [Set your file path and name accordingly]
SECRETS_DIR=$(cd ../ && echo $PWD)/Production_cutover/secrets
SECRETS_FILE=$SECRETS_DIR/.github_api_keys
while IFS= read -r line; do
  if [[ "$line" == *"GITHUB_API_TOKEN"* ]]; then
	GH_API_TOKEN=${line#*=}
    break
  fi
done < "$SECRETS_FILE"
[[ -z "$GH_API_TOKEN" ]] && echo && echo "GH_API_TOKEN not specified. Exiting." && exit 1
GH_AUTH="Authorization: token $GH_API_TOKEN"

# Get latest tag
echo && echo "Getting latest tag..."
if [[ "$GH_TAG" == 'LATEST' ]]; then
  GH_TAGS="$GH_REPO/releases/latest"
fi
echo "Retrieved tag: '$GH_TAGS'" && echo

# Package the archive
echo "Creating release package..."
if [ -f $GH_ASSET_NAME ];then
    rm $GH_ASSET_NAME
fi
cd $GH_REPO_PATH/addons
zip -r ldraw_render_addons.zip io_scene_importldraw io_scene_renderldraw -x \
"io_scene_importldraw/__pycache__/*" \
"io_scene_importldraw/images/*" \
"io_scene_importldraw/loadldraw/__pycache__/*" \
"io_scene_importldraw/LICENSE" \
"io_scene_importldraw/README.md" \
"io_scene_renderldraw/__pycache__/*"
cd ../
zip -r $GH_ASSET_NAME addons/ldraw_render_addons.zip installBlenderAddons.py
rm addons/ldraw_render_addons.zip
echo && echo "Created release package '$GH_ASSET_NAME'" && echo

# Validate token.
echo "Validating user token..." && echo
curl -o /dev/null -sH "$GH_AUTH" $GH_REPO || { echo "Error: Invalid repo, token or network issue!";  exit 1; }

# Read asset tags and display response.
echo "Retrieving repository data..." && echo
GH_RESPONSE=$(curl -sH "$GH_AUTH" $GH_TAGS)
echo "INFO: Response $GH_RESPONSE" && echo

# Get ID of the release.
echo "Retrieving release id..."
GH_RELEASE_ID="$(echo $GH_RESPONSE | jq -r .id)"
echo "Release id '$GH_RELEASE_ID'" && echo

# Get ID of the asset based on given file name.
echo "Retrieving asset id..."
GH_ASSET_ID="$(echo $GH_RESPONSE | jq -r '.assets[] | select(.name == '\"$GH_ASSET_NAME\"').id')"
if [ "$GH_ASSET_ID" = "" ]; then
    echo "Asset id for $GH_ASSET_NAME not found so no need to overwrite"
else
	echo "Asset id '$GH_ASSET_ID'" && echo
    echo "Deleting asset $GH_ASSET_NAME ($GH_ASSET_ID)..."
    curl "$GITHUB_OAUTH_BASIC" -X "DELETE" -H "$GH_AUTH" "$GH_REPO/releases/assets/$GH_ASSET_ID"
fi

# Prepare and upload the specified asset
echo && echo "Uploading asset $GH_ASSET_NAME ($GH_ASSET_ID)..."
# Construct upload URL
GH_ASSET="https://uploads.github.com/repos/$GH_OWNER/$GH_REPO_NAME/releases/$GH_RELEASE_ID/assets?name=$(basename $GH_ASSET_NAME)"
# Upload asset
curl "$GITHUB_OAUTH_BASIC" --data-binary @"$GH_ASSET_NAME" -H "$GH_AUTH" -H "Content-Type: application/octet-stream" $GH_ASSET

echo && echo "Finished." && echo
