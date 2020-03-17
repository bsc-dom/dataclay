#!/bin/bash
SCRIPTPATH=$( cd "$(dirname "$0")" ; pwd -P )
PYCLAY_PATH=`realpath $SCRIPTPATH/..`

export PYTHONPATH=$PYCLAY_PATH/src:$PYCLAY_PATH/tests:$PYTHONPATH

if ! type "pytest" > /dev/null; then
	echo "** Pytest not installed. Installing it... **"
	pip install pytest pytest-xdist pytest-html pytest-timeout 
	if [ $? -eq 0 ]; then
		echo "** OK! Pytest installed! **"
	else
	    echo "** Installation of pytest failed. Please check. Maybe you should run it with 'sudo'**"
	fi
fi

rm -f results_testing.html
rm -f results.xml
pytest --no-print-logs --boxed --junitxml results.xml $PYCLAY_PATH/tests/functional_tests/$1
