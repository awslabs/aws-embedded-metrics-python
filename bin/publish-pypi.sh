#!/usr/bin/env bash 
# usage:
#   ./.buildutils/publish-pypi.sh
#
# Installing test
# python3 -m venv venv
# source venv/bin/activate
# pip3 install --extra-index-url https://testpypi.python.org/pypi aws-embedded-metrics 

rootdir=$(git rev-parse --show-toplevel)
rootdir=${rootdir:-$(pwd)} # in case we are not in a git repository (Code Pipelines)
source $rootdir/bin/utils.sh

cd $rootdir
rm -rf dist

tox
check_exit

python3 setup.py sdist bdist_wheel
check_exit

# upload to test PyPI
if [ -v TWINE_REPOSITORY ];
then
  echo "Publishing to $TWINE_REPOSITORY";
  python3 -m twine upload --repository-url $TWINE_REPOSITORY dist/*;
else
  echo "Publishing to prod";
  python3 -m twine upload dist/*;
fi

check_exit

