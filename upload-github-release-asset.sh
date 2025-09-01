#!/usr/bin/env bash
#
# Author: Trevor SANDY
# Last Update September 01, 2025
#
# File: upload-github-release-asset.sh
#
# Adapted from original script by Stefan Buck
# License: MIT


function ShowHelp()
{
    echo
    echo "Script to upload a release asset using the GitHub API v3."
    echo
    echo "Examples:"
    echo
    echo "--Publish package to specified DevOps location and extract"
    echo "$ (cd ~/projects/blenderldrawrender && env TAG=v1.6.2 DEV_OPS=1 UNZIP=1 ./$0)"
    echo
    echo "--Publish package to GitHub release"
    echo "$ (cd ~/projects/blenderldrawrender && env TAG=v1.6.2 COMMIT_NOTE=\"Render LDraw v1.6.2\" ./$0)"
    echo
    echo "--Update the version number in .py files"
    echo "$ (cd ~/projects/blenderldrawrender && env TAG=v1.6.2 SET_VERSION=true ./$0)"
    echo
    echo "This script accepts the following parameters:"
    echo "DEV_OPS      - Build and publish packaged archive to DevOps"
    echo "NO_COMMIT    - Do not commit a new tag for DevOps build - only update .py files"
    echo "NO_UPLOAD    - Do not upload DevOps build to GitHub repository - no tag will be created"
    echo "PUBLISH_DEST - Publish the DevOps build to this destination path"
    echo "UNZIP        - Unzip the DevOps build archive package - requires PUBLISH_DEST"
    echo "TAG          - Release tag"
    echo "OWNER        - GitHub Repository owner"
    echo "RELEASE      - Release label"
    echo "COMMIT_NOTE  - Commit note"
    echo "REPO_NAME    - GitHub Repository"
    echo "REPO_PATH    - Full path to GitHub the repository"
    echo "REPO_BRANCH  - The specified GitHub repository branch"
    echo "ASSET_NAME   - Build archive package file name"
    echo "API_TOKEN    - User GitHub Token (Use a local git .config file containing your token)"
    echo "SET_VERSION  - Update the version number in .py files and exit - do not build or publish"
    echo
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -h|--help) ShowHelp; exit 0 ;;
        *) echo "Unknown parameter passed: '$1'. Use to show help."; exit 1 ;;
    esac
done

SCRIPT_NAME=$0
SCRIPT_ARGS=$*
OS_NAME=$(uname)

echo && echo "$SCRIPT_NAME" && echo

# Check for script dependencies
echo
#set -e
echo -n "Checking script dependencies... "
for name in zip python3 jq xargs
do
    [[ $(which $name 2>/dev/null) ]] || { echo -en "\n$name needs to be installed. Use 'sudo apt-get install $name'";deps=1; }
done
if [[ $deps -ne 1 ]]; then echo "OK"; else { echo -en "\nInstall the above and rerun this script\n"; exit 1;}; fi

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
GH_COMMIT_NOTE=${COMMIT_NOTE:-Render LDraw ${GH_TAG:1}}
GH_ASSET_NAME=${ASSET_NAME:-LDrawBlenderRenderAddons.zip}
GH_ASSET_SHA_NAME=${GH_ASSET_NAME}.sha256
GH_API_TOKEN=${API_TOKEN:-$(git config --global github.token)}
GH_SET_VERSION=${SET_VERSION:-false}

DEV_OPS_REL=${DEV_OPS:-}
DEV_OPS_NO_COMMIT=${NO_COMMIT:-}
DEV_OPS_NO_UPLOAD=${NO_UPLOAD:-false}
DEV_OPS_REL_UNZIP=${UNZIP:-}
DEV_OPS_PUBLISH_DEST=${PUBLISH_DEST:-/home/$GH_USER/projects/build-LPub3D-Desktop_Qt_6_9_1_MSVC2022_64bit-Debug/mainApp/64bit_debug/3rdParty/Blender}

# Define variables.
GH_DIR="$GH_REPO_PATH/.git"
GH_API="https://api.github.com"
GH_REPO="$GH_API/repos/$GH_OWNER/$GH_REPO_NAME"
GH_REMOTE="https://$GH_OWNER:$GH_API_TOKEN@github.com/$GH_OWNER/$GH_REPO_NAME.git"
GH_TAGS="$GH_REPO/releases/tags/$GH_TAG"
GH_AUTH="Authorization: token $GH_API_TOKEN"
TAG_EXIST=""

# Arguments display
function display_arguments()
{
    echo
    echo "--Command Options:"
    [ -n "$SCRIPT_ARGS" ] && echo "--SCRIPT_ARGS...$SCRIPT_ARGS" || true
    echo "--TAG.............$GH_TAG"
    if [ "$GH_SET_VERSION" = "true" ]; then
        echo "--SET_VERSION.....True"
    else
        echo "--OWNER...........$GH_OWNER"
        echo "--REPO_NAME.......$GH_REPO_NAME"
        echo "--REPO_PATH.......$GH_REPO_PATH"
        echo "--REPO_BRANCH.....$GH_REPO_BRANCH"
        echo "--ASSET_NAME......$GH_ASSET_NAME"
        if [ -z "$TAG_EXIST" ]; then
            echo "--RELEASE.........$GH_RELEASE"
            echo "--RELEASE_TYPE....New Release Will Be Created"
        fi
        if [ -z "$DEV_OPS_NO_COMMIT" ]; then
            echo "--COMMIT_NOTE.....$GH_COMMIT_NOTE"
            echo "--COMMIT CHANGES..True"
        else
            echo "--COMMIT CHANGES..False"
        fi
        if [ -n "$DEV_OPS_REL" ]; then
            DEV_OPS_NO_UPLOAD=true
            echo "--PUBLISH.........Publish Release To Dev Ops"
            [ -n "$DEV_OPS_REL_UNZIP" ] && echo "--INSTALL.........Unzip DevOps Release" || true
            echo "--DEV_OPS_DEST....$DEV_OPS_PUBLISH_DEST"
        fi
        if [ "$DEV_OPS_NO_UPLOAD" = "true" ]; then
            echo "--PUBLISH.........Release Not Published"
            echo "--UPLOAD_TO_GH....False"
        else
            echo "--PUBLISH.........Publish Release To Github"
            echo "--UPLOAD_TO_GH....True"
        fi

        echo "--GH_TAGS.........$GH_TAGS"
    fi
    echo
}

# New release data
function generate_release_post_data()
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

function mv_exr ()
{
    dir="$2" # Include a / at the end to indicate directory (not filename)
    tmp="$2"; tmp="${tmp: -1}"
    [ "$tmp" != "/" ] && dir="$(dirname "$2")" || :
    [ -a "$dir" ] || mkdir -p "$dir"
    mv "$@"
}

# Package the archive
function package_archive()
{
    echo && echo "Creating release package..."
    if [ -f "$GH_ASSET_NAME" ];then
        rm "$GH_ASSET_NAME"
    fi
    cd "$GH_REPO_PATH" || :

    mv_exr addons/io_scene_import_ldraw/loadldraw/background.exr exr/ && \
    mv_exr background.exr addons/io_scene_import_ldraw/loadldraw/ && \
    echo && echo "  Replaced background.exr LFS link." && echo

    zip -r "$GH_ASSET_NAME"  \
    setup \
    addons/io_scene_import_ldraw/ \
    addons/io_scene_import_ldraw_mm/ \
    addons/io_scene_render_ldraw/ \
    install_blender_ldraw_addons.py -x \
    "addons/io_scene_import_ldraw/loadldraw/__pycache__/*" \
    "addons/io_scene_import_ldraw/__pycache__/*" \
    "addons/io_scene_import_ldraw/.gitignore" \
    "addons/io_scene_import_ldraw/.gitattributes" \
    "addons/io_scene_import_ldraw/README.md" \
    "addons/io_scene_import_ldraw_mm/__pycache__/*" \
    "addons/io_scene_import_ldraw_mm/examples/*" \
    "addons/io_scene_import_ldraw_mm/_deploy.py" \
    "addons/io_scene_import_ldraw_mm/.gitignore" \
    "addons/io_scene_import_ldraw_mm/.gitattributes" \
    "addons/io_scene_import_ldraw_mm/Readme.md" \
    "addons/io_scene_render_ldraw/__pycache__/*" \
    "addons/io_scene_render_ldraw/modelglobals/__pycache__/*" \
    "setup/addon_setup/config/LDrawRendererPreferences.ini" \
    "setup/addon_setup/__pycache__/*"

    mv_exr addons/io_scene_import_ldraw/loadldraw/background.exr ./  && \
    mv_exr exr/background.exr addons/io_scene_import_ldraw/loadldraw/ && \
    rm -r exr/ && \
    echo && echo "  Restored background.exr LFS link."
    echo && echo "Created release package '$GH_ASSET_NAME'" && echo
}

# Set working directory
cd "$GH_REPO_PATH" || :

# Logger
ME="$(basename "$(test -L "$0" && readlink "$0" || echo "$0")")"
CWD=$(pwd)
f="${CWD}/$ME"
ext=".log"
if [[ -e "$f$ext" ]] ; then
    i=1
    f="${f%.*}";
    while [[ -e "${f}_${i}${ext}" ]]; do
      (( i++ ))
    done
    f="${f}_${i}${ext}"
    else
    f="${f}${ext}"
fi
# Output log file
LOG="$f"
exec > >(tee -a "${LOG}" )
exec 2> >(tee -a "${LOG}" >&2)

# Get tag
echo && echo -n "Fetch tags... "
GIT_DIR=$GH_DIR git fetch --tags >/dev/null 2>&1
if [ "$?" = "0" ]; then echo "Ok"; else echo "Failed"; fi
VER_TAG=$(GIT_DIR=$GH_DIR git describe --tags --match v* --abbrev=0)
if [[ "$GH_TAG" == 'LATEST' ]]; then
    echo && echo -n "Setting latest tag... "
    GH_TAGS="$GH_REPO/releases/latest"
    GH_TAG=$VER_TAG
    TAG_EXIST=$GH_TAG
    echo "$VER_TAG"
else
    echo && echo -n "Getting specified tag... "
    VER_TAG=$GH_TAG
    if GIT_DIR=$GH_DIR git rev-parse "$GH_TAG" >/dev/null 2>&1; then
        TAG_EXIST=$GH_TAG
        echo "$VER_TAG"
    else
        echo tag "$VER_TAG" not found - will be created.
    fi
fi

# Show options
display_arguments

# Confirmation
sleep 1s && read -p "  Are you sure (y/n)? " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]];then
    if [[ "$0" = "${BASH_SOURCE[0]}" ]]; then exit 1; else return 1; fi # handle exits from shell or function but don't exit interactive shell
fi
echo
# Validate API Token [Place token in git config "git config --global github.token YOUR_TOKEN"]
[[ -z "$GH_API_TOKEN" ]] && echo && echo "GH_API_TOKEN not specified. Exiting." && exit 1

# Update version information
PY_VER=${VER_TAG//./", "} # replace . with ", "
PY_VER=${PY_VER/v/}      # replace v with ""
echo "Updating .py files to version $PY_VER"
for PY_FILE in addons/io_scene_import_ldraw/__*.py addons/io_scene_import_ldraw_mm/__*.py addons/io_scene_render_ldraw/__*.py;
do
    echo "  Set version to '$PY_VER' in file '$PY_FILE'"
    if [[ -f ${PY_FILE} && -r ${PY_FILE} ]]
    then
        if [ "$OS_NAME" = Darwin ]
        then
            sed -i "" -e "s/^version = (.*/version = ($PY_VER)/" \                           #__version__.py
                      -e "s/^    \"version\": (.*/    \"version\": ($PY_VER),/" "${PY_FILE}" #__init__.py
        else
            sed -i -e "s/^version = (.*/version = ($PY_VER)/" \
                   -e "s/^    \"version\": (.*/    \"version\": ($PY_VER),/" "${PY_FILE}"
        fi
    else
        echo "ERROR: Cannot read ${PY_FILE} from ${GH_REPO_PATH}"
    fi
done

if [ "$GH_SET_VERSION" = "true" ]; then
    echo && echo "Finished." && echo
    exit 1
fi

# Package the archive
package_archive

if [[ -n $DEV_OPS_REL && -f $GH_ASSET_NAME ]]; then
    declare -r p=Publish
    DEV_OPS_PUBLISH_SRC=$PWD
    DEV_OPS_NO_UPLOAD=true
    echo -n "Publish package '$GH_ASSET_NAME' to Dev Ops..." && \
    ([ -d "$DEV_OPS_PUBLISH_DEST" ] || mkdir -p "$DEV_OPS_PUBLISH_DEST"; \
     cd "$DEV_OPS_PUBLISH_DEST" && [ -n "$DEV_OPS_REL_UNZIP" ] && \
     rm -rf setup addons *.zip *_addons.py || :; \
     cp -f "$DEV_OPS_PUBLISH_SRC/$GH_ASSET_NAME" . || exit 1) >$p.out 2>&1 && rm $p.out
    [ -f $p.out ] && echo "ERROR - failed to publish $GH_ASSET_NAME to Dev Ops" && \
    tail -80 $p.out || echo "Success." && \
    echo "Publish Destination: $DEV_OPS_PUBLISH_DEST"

    if [ -n "$DEV_OPS_REL_UNZIP" ]; then
        echo -n "Extract $GH_ASSET_NAME..."
        if [ -f "$DEV_OPS_PUBLISH_DEST/$GH_ASSET_NAME" ]; then
            (cd "$DEV_OPS_PUBLISH_DEST" && python3 -m zipfile -e $GH_ASSET_NAME . || exit 1) >$p.out 2>&1 && rm $p.out
            [ -f $p.out ] && echo "Failed." && tail -80 $p.out || echo "Success."
        else
            echo "Failed - $GH_ASSET_NAME not found."
        fi
    fi
fi

# Validate token.
if [ "$DEV_OPS_NO_UPLOAD" != "true" ]; then
    echo -n "Validating user token..."
    curl -o /dev/null -sH "$GH_AUTH" "$GH_REPO"
    if [ "$?" = "0" ]; then
        echo "Ok"
    else
        echo "ERROR: Invalid repo, token or network issue!"
        exit 1
    fi
fi

# Create version commit
if [ -z "$DEV_OPS_NO_COMMIT" ]; then
    echo && echo -n "Converting files from CRLF to LF... " && \
    ( find . \
    -not -path "./.git/*" \
    -not -path "./.vscode/*" \
    -not -wholename '*loadldraw/__init__.py' \
    -not -wholename '*modelglobals/__init__.py' \
    -not -wholename '*config/.keep' \
    -not -name '*.blend' \
    -not -name '*.png' \
    -not -name '*.jpg' \
    -not -name '*.exr' \
    -not -name '*.pdf' \
    -not -name '*.zip' \
    -not -name '*.gif' \
    -type f -print0 | xargs -0 dos2unix -q ) && \
    echo "Done" || echo "Failed"
    # Commit changed files
    echo && echo "Commit changed files..."
    git add .
cat << pbEOF >$GH_DIR/COMMIT_EDITMSG
$GH_COMMIT_NOTE

pbEOF
    GIT_DIR=$GH_DIR git commit -m "$GH_COMMIT_NOTE"
    # Push committed files to remote master
    if [ "$DEV_OPS_NO_UPLOAD" != "true" ]; then git push -u $GH_REMOTE master >/dev/null; fi
fi

# Stop here if not uploading build
if [ "$DEV_OPS_NO_UPLOAD" = "true" ]; then echo && echo "Finished." && echo && exit 0; fi

# Set latest tag or create release tag if specified tag does not exist
if [[ -z "$TAG_EXIST" ]]; then
    echo && echo "Create release '$GH_RELEASE', version '$GH_TAG', for repo '$GH_REPO_NAME' on branch '$GH_REPO_BRANCH'" && echo
    curl -H "$GH_AUTH" --data "$(generate_release_post_data)" "$GH_REPO/releases"
    GIT_DIR=$GH_DIR git fetch --tags
    VER_TAG=$(GIT_DIR=$GH_DIR git describe --tags --match v* --abbrev=0)
fi
# VER_TAG=$GH_TAG    #ENABLE FOR TEST
echo && echo "Retrieved tag: '$GH_TAG'" && echo

# Read asset tags and display response.
echo "Retrieving repository data..." && echo
GH_RESPONSE=$(curl -sH "$GH_AUTH" "$GH_TAGS")
echo "INFO: Response $GH_RESPONSE" && echo

# Release was not found so create it
GH_RELEASE_NOT_FOUND=$(echo -e "$GH_RESPONSE" | sed -n '2p')
if [[ "$GH_RELEASE_NOT_FOUND" == *"Not Found"* ]]; then
    echo && echo "Release not found. Creating release '$GH_RELEASE', version '$GH_TAG', for repo '$GH_REPO_NAME' on branch '$GH_REPO_BRANCH'..." && echo
    GH_COMMIT_NOTE=$(git log -1 --pretty=%B)
    curl -H "$GH_AUTH" --data "$(generate_release_post_data)" "$GH_REPO/releases"
    GH_RESPONSE=$(curl -sH "$GH_AUTH" "$GH_TAGS")
fi

# Get ID of the release.
echo && echo -n "Retrieving release id... "
GH_RELEASE_ID=$(echo "$GH_RESPONSE" | jq -r .id)
echo "Release id: '$GH_RELEASE_ID'"

# Get ID of the asset based on given file name.
echo && echo -n "Retrieving asset id... "
GH_ASSET_ID="$(echo "$GH_RESPONSE" | jq -r '.assets[] | select(.name == '\""$GH_ASSET_NAME"\"').id')"
if [ "$GH_ASSET_ID" = "" ]; then
    echo "Asset id for $GH_ASSET_NAME not found so no need to overwrite"
else
    echo "Asset id: '$GH_ASSET_ID'" && echo
    echo "Deleting asset $GH_ASSET_NAME ($GH_ASSET_ID)..."
    curl -X "DELETE" -H "$GH_AUTH" "$GH_REPO/releases/assets/$GH_ASSET_ID"
fi

# Get ID of the asset sha based on given file name.
echo && echo -n "Retrieving asset sha id... "
GH_ASSET_SHA_ID="$(echo $GH_RESPONSE | jq -r '.assets[] | select(.name == '\"$GH_ASSET_SHA_NAME\"').id')"
if [ "$GH_ASSET_SHA_ID" = "" ]; then
    echo "Asset id for $GH_ASSET_SHA_NAME not found so no need to overwrite"
else
    echo "Asset id: '$GH_ASSET_SHA_ID'" && echo
    echo "Deleting asset sha $GH_ASSET_SHA_NAME ($GH_ASSET_SHA_ID)..."
    curl -X "DELETE" -H "$GH_AUTH" "$GH_REPO/releases/assets/$GH_ASSET_SHA_ID"
fi

# Prepare SHA hash file
echo && echo -n "Creating $GH_ASSET_SHA_NAME hash file..."
sha256sum "$GH_ASSET_NAME" > "$GH_ASSET_SHA_NAME" && echo "OK" || \
echo "ERROR - Failed"

# Prepare and upload the asset and respective asset sha files
if [[ -f "$GH_ASSET_NAME" && -f "$GH_ASSET_SHA_NAME" ]]; then

    echo && echo "Uploading asset sha $GH_ASSET_SHA_NAME, ID: $GH_ASSET_SHA_ID..."

    GH_ASSET_URL=https://uploads.github.com/repos/$GH_OWNER/$GH_REPO_NAME/releases/$GH_RELEASE_ID/assets

    GH_ASSET="${GH_ASSET_URL}?name=$(basename "$GH_ASSET_NAME").sha256"

    curl --data-binary @"$GH_ASSET_SHA_NAME" -H "$GH_AUTH" -H "Content-Type: text/xml" "$GH_ASSET"

    echo && echo "Uploading asset $GH_ASSET_NAME, ID: $GH_ASSET_ID..."

    GH_ASSET="${GH_ASSET_URL}?name=$(basename "$GH_ASSET_NAME")"

    curl --data-binary @"$GH_ASSET_NAME" -H "$GH_AUTH" -H "Content-Type: application/octet-stream" "$GH_ASSET"

else

    echo && echo "ERROR - Could not find $GH_ASSET_SHA_NAME or $GH_ASSET_NAME - No upload performed."

fi

echo && echo "Finished." && echo
