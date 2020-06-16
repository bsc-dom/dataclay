#!/bin/bash

if [ "$TRAVIS_BRANCH" == "master" ]; then 
     export GIT_TAG=$(cat VERSION.txt)
     git tag $GIT_TAG -a -m "New release"
     git push origin $GIT_TAG
else
     echo "Skipping Git tag because current branch is not master"
fi
