#!/usr/bin/env bash
#
# Author: Trevor SANDY
# Last Update May 06, 2023
#
# Adapted from original script by Stefan Buck
# License: MIT
#
# Script to upload a release asset using the GitHub API v3.
#
# Example:
#
# cd /home/trevorsandy/projects/blenderldrawrender
#
# env TAG=v1.3.0 SET_VERSION=True ./upload-github-release-asset.sh
#
# env TAG=v1.3.7 RELEASE_NOTE="Render LDraw v1.3.7" ./upload-github-release-asset.sh
#
# This script accepts the following parameters:
# TAG             - Release tag
# OWNER           - Repository owner
# RELEASE         - Release label
# RELEASE_NOTE    - Release note
# REPO_NAME       - Repository
# REPO_PATH       - Full path to the repository
# REPO_BRANCH     - The specified repository branch
# ASSET_NAME      - File name
# API_TOKEN       - User GitHub Token (Use a local file containing your token)
# SET_VERSION     - Update the version number in .py files and exit
#

SCRIPT_NAME=$0
SCRIPT_ARGS=$*
HOME_DIR=$PWD
OS_NAME=`uname`

echo && echo $SCRIPT_NAME && echo

# Check for script dependencies
echo
#set -e
echo -n "Checking dependencies... "
for name in zip jq xargs
do
    [[ $(which $name 2>/dev/null) ]] || { echo -en "\n$name needs to be installed. Use 'sudo apt-get install $name'";deps=1; }
done
[[ $deps -ne 1 ]] && echo "OK" || { echo -en "\nInstall the above and rerun this script\n";exit 1; }

# Validate settings.
[ "$TRACE" ] && set -x

# Arguments
GH_TAG=${TAG:-LATEST}
GH_OWNER=${OWNER:-trevorsandy}
GH_USER=${USER:-trevor}
GH_REPO_NAME=${REPO_NAME:-blenderldrawrender}
GH_REPO_BRANCH=${REPO_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}
GH_REPO_PATH=${REPO_PATH:-/home/$GH_USER/projects/$GH_REPO_NAME}
GH_RELEASE=${RELEASE:-Blender LDraw Render $(date +%d.%m.%Y)}
GH_RELEASE_NOTE=${RELEASE_NOTE:-Initial release}
GH_ASSET_NAME=${ASSET_NAME:-LDrawBlenderRenderAddons.zip}
GH_API_TOKEN=${API_TOKEN:-$(git config --global github.token)}
GH_SET_VERSION=${SET_VERSION:-False}

# Define variables.
GH_API="https://api.github.com"
GH_REPO="$GH_API/repos/$GH_OWNER/$GH_REPO_NAME"
GH_TAGS="$GH_REPO/releases/tags/$GH_TAG"
GH_AUTH="Authorization: token $GH_API_TOKEN"
WGET_ARGS="--content-disposition --auth-no-challenge --no-cookie"
CURL_ARGS="-LJO#"
TAG_EXIST=""

# Arguments display
function display_arguments
{
    echo
    echo "--Command Options:"
    [ -n "$SCRIPT_ARGS" ] && echo "--SCRIPT_ARGS...$SCRIPT_ARGS" || true
    echo "--TAG...........$GH_TAG"
    if [ "$GH_SET_VERSION" = "True" ]; then
        echo "--SET_VERSION...$GH_SET_VERSION"
    else
        echo "--OWNER.........$GH_OWNER"
        echo "--REPO_NAME.....$GH_REPO_NAME"
        echo "--REPO_PATH.....$GH_REPO_PATH"
        echo "--REPO_BRANCH...$GH_REPO_BRANCH"
        echo "--ASSET_NAME....$GH_ASSET_NAME"
        if [ -z "$TAG_EXIST" ]; then
            echo "--RELEASE.......$GH_RELEASE"
            echo "--RELEASE_NOTE..$GH_RELEASE_NOTE"
            echo "--NEW RELEASE WILL BE CREATED"
        fi
        echo "--GH_TAGS.......$GH_TAGS"
    fi
    echo
}

# New release data
function generate_release_post_data
{
  cat <<EOF
{
  "tag_name": "$GH_TAG",
  "target_commitish": "$GH_REPO_BRANCH",
  "name": "$GH_RELEASE",
  "body": "$GH_RELEASE_NOTE",
  "draft": false,
  "prerelease": false
}
EOF
}

# Package the archive
function package_archive
{
    echo && echo "Creating release package..."
    if [ -f $GH_ASSET_NAME ];then
        rm $GH_ASSET_NAME
    fi
    cd $GH_REPO_PATH
    zip -r $GH_ASSET_NAME  \
    setup \
    addons/io_scene_lpub3d_importldraw/ \
    addons/io_scene_lpub3d_importldraw_mm/ \
    addons/io_scene_lpub3d_renderldraw/ \
    install_blender_ldraw_addons.py -x \
    "addons/io_scene_lpub3d_importldraw/loadldraw/__pycache__/*" \
    "addons/io_scene_lpub3d_importldraw/__pycache__/*" \
    "addons/io_scene_lpub3d_importldraw/.gitignore" \
    "addons/io_scene_lpub3d_importldraw/.gitattributes" \
    "addons/io_scene_lpub3d_importldraw/README.md" \
    "addons/io_scene_lpub3d_importldraw_mm/__pycache__/*" \
    "addons/io_scene_lpub3d_importldraw_mm/examples/*" \
    "addons/io_scene_lpub3d_importldraw_mm/_deploy.py" \
    "addons/io_scene_lpub3d_importldraw_mm/.gitignore" \
    "addons/io_scene_lpub3d_importldraw_mm/.gitattributes" \
    "addons/io_scene_lpub3d_importldraw_mm/Readme.md" \
    "addons/io_scene_lpub3d_renderldraw/__pycache__/*" \
    "addons/io_scene_lpub3d_renderldraw/modelglobals/__pycache__/*" \
    "setup/addon_setup/config/LDrawRendererPreferences.ini" \
    "setup/addon_setup/__pycache__/*"
    echo && echo "Created release package '$GH_ASSET_NAME'" && echo
}

# Set working directory
cd $GH_REPO_PATH

# Logger
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
# Output log file
LOG="$f"
exec > >(tee -a ${LOG} )
exec 2> >(tee -a ${LOG} >&2)

# Get tag
#GIT_DIR=$GH_REPO_PATH/.git git fetch --tags
VER_TAG=`GIT_DIR=$GH_REPO_PATH/.git git describe --tags --match v* --abbrev=0`
if [[ "$GH_TAG" == 'LATEST' ]]; then
    echo && echo -n "Setting latest tag... "
    GH_TAGS="$GH_REPO/releases/latest"
    GH_TAG=$VER_TAG
    TAG_EXIST=$GH_TAG
    echo $VER_TAG
else
    echo && echo -n "Getting specified tag... "
    VER_TAG=$GH_TAG
    if GIT_DIR=$GH_REPO_PATH/.git git rev-parse $GH_TAG >/dev/null 2>&1; then
        TAG_EXIST=$GH_TAG
        echo $VER_TAG
    else
        echo tag $VER_TAG not found - will be created.
    fi
fi

# Show options
display_arguments

# Confirmation
sleep 1s && read -p "  Are you sure (y/n)? " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]];then
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1 # handle exits from shell or function but don't exit interactive shell
fi
echo
# Validate API Token [Place token in git config "git config --global github.token YOUR_TOKEN"]
#[[ -z "$GH_API_TOKEN" ]] && echo && echo "GH_API_TOKEN not specified. Exiting." && exit 1

# Update version information
VER_TAG=${VER_TAG//./", "} # replace . with ", "
VER_TAG=${VER_TAG/v/}      # replace v with ""
echo "Updating .py files to version $VER_TAG"
for GH_FILE in addons/io_scene_lpub3d_importldraw/__*.py addons/io_scene_lpub3d_importldraw_mm/__*.py addons/io_scene_lpub3d_renderldraw/__*.py;
do
    echo "Set version to '$VER_TAG' in file '$GH_FILE'"
    if [ -f ${GH_FILE} -a -r ${GH_FILE} ]
    then
        if [ "$OS_NAME" = Darwin ]
        then
            sed -i "" -e "s/^version = (.*/version = ($VER_TAG)/" \                           #__version__.py
                      -e "s/^    \"version\": (.*/    \"version\": ($VER_TAG),/" "${GH_FILE}" #__init__.py
        else
            sed -i -e "s/^version = (.*/version = ($VER_TAG)/" \
                   -e "s/^    \"version\": (.*/    \"version\": ($VER_TAG),/" "${GH_FILE}"
        fi
    else
        echo "ERROR: Cannot read ${GH_FILE} from ${GH_REPO_PATH}"
    fi
done

if [ "$GH_SET_VERSION" = "True" ]; then
    echo && echo "Finished." && echo
    exit 1
fi

# Package the archive
package_archive

# Publish the archive to dev env (Set DEV_USE=1 to enable)
DEV_USE=1

if [[ -n $DEV_USE && -f $GH_ASSET_NAME ]]; then
    declare -r p=Publish
    PUBLISH_SRC=$PWD
    PUBLISH_DEST="/home/$GH_USER/projects/build-LPub3D-Desktop_Qt_5_15_2_MSVC2019_32bit-Debug/mainApp/32bit_debug/3rdParty/Blender"
    echo -n "Publish package '$GH_ASSET_NAME' to Dev Env..." && \
    ([ -d "$PUBLISH_DEST" ] || mkdir -p "$PUBLISH_DEST"; \
     cd "$PUBLISH_DEST" && cp -f "$PUBLISH_SRC/$GH_ASSET_NAME" .) >$p.out 2>&1 && rm $p.out
    [ -f $p.out ] && echo "ERROR - failed to publish $GH_ASSET_NAME to Dev Env" && tail -80 $p.out || echo "Success."
#	rm "$PUBLISH_SRC/$GH_ASSET_NAME" || true
    rm "$LOG"
    exit 1
fi

# Commit changed files
echo && echo "Commit changed files..."
git add .
GH_RELEASE_NOTE="LPub3D Render LDraw $VER_TAG"
cat << pbEOF >$GH_DIR/COMMIT_EDITMSG
$GH_RELEASE_NOTE

pbEOF
GIT_DIR=$GH_REPO_PATH/.git git commit -m "$GH_RELEASE_NOTE"

# Set latest tag or create release if specified tag does not exist
if [[ -z "$TAG_EXIST" ]]; then
    echo && echo "Create release '$GH_RELEASE', version '$GH_TAG', for repo '$GH_REPO_NAME' on branch '$GH_REPO_BRANCH'" && echo
    curl --data "$(generate_release_post_data)" "$GH_REPO/releases?access_token=$GH_API_TOKEN"
    GIT_DIR=$GH_REPO_PATH/.git git fetch --tags
    VER_TAG=`GIT_DIR=$GH_REPO_PATH/.git git describe --tags --match v* --abbrev=0`
fi
# VER_TAG=$GH_TAG    #ENABLE FOR TEST
echo && echo "Retrieved tag: '$GH_TAG'" && echo

# Validate token.
echo "Validating user token..." && echo
curl -o /dev/null -sH "$GH_AUTH" $GH_REPO || { echo "ERROR: Invalid repo, token or network issue!";  exit 1; }

# Read asset tags and display response.
echo "Retrieving repository data..." && echo
GH_RESPONSE=$(curl -sH "$GH_AUTH" $GH_TAGS)
echo "INFO: Response $GH_RESPONSE" && echo

# Release was not found so create it
GH_RELEASE_NOT_FOUND=$(echo -e "$GH_RESPONSE" | sed -n '2p')
if [[ "$GH_RELEASE_NOT_FOUND" == *"Not Found"* ]]; then
    echo && echo "Release not found. Creating release '$GH_RELEASE', version '$GH_TAG', for repo '$GH_REPO_NAME' on branch '$GH_REPO_BRANCH'..." && echo
    GH_RELEASE_NOTE=$(git log -1 --pretty=%B)
    curl --data "$(generate_release_post_data)" "$GH_REPO/releases?access_token=$GH_API_TOKEN"
    GH_RESPONSE=$(curl -sH "$GH_AUTH" $GH_TAGS)
fi

# Get ID of the release.
echo && echo -n "Retrieving release id... "
GH_RELEASE_ID="$(echo $GH_RESPONSE | jq -r .id)"
echo "Release id: '$GH_RELEASE_ID'"

# Get ID of the asset based on given file name.
echo && echo -n "Retrieving asset id... "
GH_ASSET_ID="$(echo $GH_RESPONSE | jq -r '.assets[] | select(.name == '\"$GH_ASSET_NAME\"').id')"
if [ "$GH_ASSET_ID" = "" ]; then
    echo "Asset id for $GH_ASSET_NAME not found so no need to overwrite"
else
    echo "Asset id: '$GH_ASSET_ID'" && echo
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
