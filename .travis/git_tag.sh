#!/bin/bash

if [ "$TRAVIS_BRANCH" == "master" ]; then 
     export GIT_TAG=$(cat VERSION.txt)
     git tag $GIT_TAG -a -m "Generated tag from TravisCI build $TRAVIS_BUILD_NUMBER"
     git push origin $GIT_TAG
else
     echo "Skipping Git tag because current branch is not master"
fi
