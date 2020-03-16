#!/bin/bash
red=$'\e[1;91m'
grn=$'\e[1;32m'
end=$'\e[0m'

if [[ $TRAVIS_BRANCH == 'master' ]]; then 
     echo "$grn OK: Branch name accomplishes branch naming conventions [master] $end"
elif [[ $TRAVIS_BRANCH == 'develop' ]]; then 
     echo "$grn OK: Branch name accomplishes branch naming conventions [develop] $end"
else
    valid_branch_regex="^(feature|bugfix|improvement|library|prerelease|release|hotfix)\/[a-z0-9._-]+$"
    if [[ ! $TRAVIS_BRANCH =~ $valid_branch_regex ]]; then
        echo "$red ERROR: There is something wrong with your branch name. Branch names in this project must adhere to this contract: $valid_branch_regex. Your PR will be rejected. You should rename your branch to a valid name and try again. $end"
        exit 1
    else 
        echo "$grn OK: Branch name accomplishes branch naming conventions $end"
    fi
fi
