#!/bin/sh -xe

# Thanks to:
# https://djw8605.github.io/2016/05/03/building-centos-packages-on-travisci/
# https://github.com/opensciencegrid/htcondor-ce/tree/master/tests

# Version of CentOS/RHEL
OS_VERSION=$1
PY_VER=$2
DOCKER_IMAGE=$3
ROOT_VER=$4

## drive the different options here, passed in from the parent?
# setBuildEnv.sh -p ${PYTHON_VERSION} -c ${COMPILER_VERSION}
if [ ! -z ${1+x} ]
then
    eval "$1"
fi
