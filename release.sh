#!/bin/bash
set -e
#-----------------------------------------------------------------------
# Helper functions (miscellaneous)
#-----------------------------------------------------------------------
CONSOLE_CYAN="\033[1m\033[36m"; CONSOLE_NORMAL="\033[0m"; CONSOLE_RED="\033[1m\033[91m"
printMsg() {
  printf "${CONSOLE_CYAN}${1}${CONSOLE_NORMAL}\n"
}
printError() {
  printf "${CONSOLE_RED}${1}${CONSOLE_NORMAL}\n"
  exit 1
}
#-----------------------------------------------------------------------
# MAIN
#-----------------------------------------------------------------------
DEV=false
PROMPT=true
BRANCH_TO_CHECK="master"
while test $# -gt 0
do
    case "$1" in
        --dev)
          DEV=true
          BRANCH_TO_CHECK="develop"
            ;;
        -y)
        	PROMPT=false
        	;;
        *) echo "Bad option $1"
        	exit 1
            ;;
    esac
    shift
done


VERSION=$(cat VERSION.txt)
printMsg "Welcome to pyClay release script"
GIT_BRANCH=$(git name-rev --name-only HEAD)
if [[ "$GIT_BRANCH" != "$BRANCH_TO_CHECK" ]]; then
  printError "Branch is not $BRANCH_TO_CHECK. Aborting script"
fi

if [ "$PROMPT" = true ]; then

  read -p "Version defined is $VERSION. Is this ok? (y/n) " -n 1 -r
  echo    # (optional) move to a new line
  if [[ ! $REPLY =~ ^[Yy]$ ]]
  then
      printError "Please modify VERSION.txt file"
  fi

  printf "${CONSOLE_RED} IMPORTANT: you're about to build and officially release pyclay $VERSION ${CONSOLE_NORMAL}\n"
  read -rsn1 -p" Press any key to continue (CTRL-C for quitting this script)";echo

fi

if [ ! -d venv ]; then
    printError "Please create virtual environment at ./venv"
    exit 1
fi

source venv/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools twine SecretStorage keyring wheel keyrings.alt

# Clean
rm -rf dist build src/dataClay.egg-info

if [ "$DEV" = true ] ; then

  python setup.py egg_info --tag-build=dev --tag-date -q clean --all install sdist bdist_wheel
  twine upload --skip-existing -r pypitest dist/* || printError "Make sure to have pypitest entry in ~/.pypirc with username and password"
  #--repository-url https://test.pypi.org/legacy/ dist/*

else

  python setup.py -q clean --all install sdist bdist_wheel
  twine upload dist/* || printError "Make sure to have proper ~/.pypirc username and password"

  printMsg "Post-processing files in master"
  PREV_VERSION=$(echo "$VERSION - 0.1" | bc)
  NEW_VERSION=$(echo "$VERSION + 0.1" | bc)
  GIT_TAG=$VERSION
  echo $NEW_VERSION > VERSION.txt

  # Modify README.md
  sed -i "s/$VERSION/$NEW_VERSION/g" README.md
  sed -i "s/$PREV_VERSION/$VERSION/g" README.md
  git add README.md
  git commit -m "Release ${GIT_TAG}"
  git push origin master

  printMsg "Tagging new release in Git"
  git tag -a ${GIT_TAG} -m "Release ${GIT_TAG}"
  git push origin ${GIT_TAG}

  printMsg "Preparing develop branch"
  ## update develop branch also ##
  git fetch --all
  git checkout develop
  git merge master
  git add VERSION.txt
  git commit -m "Updating version.txt"
  git push origin develop

    # back to master
  git checkout master
fi
deactivate
printMsg "  ==  Everything seems to be ok! Bye"