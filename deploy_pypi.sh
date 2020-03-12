#!/bin/bash
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
grn=$'\e[1;32m'
blu=$'\e[1;34m'
red=$'\e[1;91m'
end=$'\e[0m'
function printMsg { 
  echo "${blu}[dataClay deploy] $1 ${end}"
}
function printError { 
  echo "${red}======== $1 ========${end}"
}

################################## OPTIONS #############################################

DEV=false

# idiomatic parameter and option handling in sh
while test $# -gt 0
do
    case "$1" in
        --dev) DEV=true
            ;;
        --*) echo "bad option $1"
        	exit -1
            ;;
        *) echo "bad option $1"
        	exit -1
            ;;
    esac
    shift
done

if [ "$DEV" = false ] ; then
	GIT_BRANCH=$(git name-rev --name-only HEAD)
	if [[ "$GIT_BRANCH" != "master" ]]; then
	  echo 'Aborting deployment, only master branch can deploy a release';
	  exit 1;
	fi
fi

################################## VERSIONING #############################################
DEFAULT_PYTHON=3.7

################################## FUNCTIONS #############################################

pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}


################################## MAIN #############################################


printMsg "'"'
      _       _         _____ _             
     | |     | |       / ____| |            
   __| | __ _| |_ __ _| |    | | __ _ _   _ 
  / _` |/ _` | __/ _` | |    | |/ _` | | | |
 | (_| | (_| | || (_| | |____| | (_| | |_| |  pypi release script
  \__,_|\__,_|\__\__,_|\_____|_|\__,_|\__, |
                                       __/ |
                                      |___/ 
'"'"
printMsg " Welcome to dataClay Pypi release script!"

################################## VERSIONS #############################################

if [ "$DEV" = false ] ; then
	while true; do
		version=`grep -m 1 "version" $SCRIPTDIR/dspython/pyclay/setup.py`
		echo "Current defined version in setup.py: $grn $version $end" 
		read -p "Are you sure setup.py version is correct (yes/no)? " yn
		case $yn in
			[Yy]* ) break;;
			[Nn]* ) echo "Modify it and try again."; exit;;
			* ) echo "$red Please answer yes or no. $end";;
		esac
	done
fi
################################## PUSH #############################################

# If develop, check if pypi already has a package 
if [ "$DEV" = true ] ; then
	PACKAGE_JSON_URL="https://pypi.org/pypi/dataClay/json"
	TODAY=$(date +'%Y%m%d')
	PYPI_PACKAGES=$(curl -s "$PACKAGE_JSON_URL" | jq  -r '.releases | keys | .[]' | sort -V | grep $TODAY | wc -l)	
	if [[ "$PYPI_PACKAGES" -ne 0 ]]; then
		echo "Already pushed in pypi"
		exit 0
	fi
fi


printMsg " ==== Pushing dataclay to Pypi ===== "
# Upload pyclay
VIRTUAL_ENV=/tmp/venv_pyclay
rm -rf $VIRTUAL_ENV
echo " Creating virtual environment /tmp/venv_pyclay " 
virtualenv --python=/usr/bin/python${DEFAULT_PYTHON} $VIRTUAL_ENV
echo " Calling python installation in virtual environment $VIRTUAL_ENV " 
source $VIRTUAL_ENV/bin/activate
python3 -m pip install --upgrade setuptools wheel twine
echo " * IMPORTANT: please make sure to remove build, dist and src/dataClay.egg if permission denied * " 
echo " * IMPORTANT: please make sure libyaml-dev libpython2.7-dev python-dev python3-dev python3-pip packages are installed * " 
python3 -m pip install -r requirements.txt
rm -rf dist
if [ "$DEV" = true ] ; then
	python3 setup.py egg_info --tag-build=dev --tag-date -q clean --all install sdist bdist_wheel
else 
	python3 setup.py -q clean --all install sdist bdist_wheel
fi

if [ $? -ne 0 ]; then
	echo "ERROR: error installing pyclay"
	exit -1
fi 	
twine upload dist/*
deactivate

printMsg " ===== Done! ====="
