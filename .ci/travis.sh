#!/bin/sh -xe

# Thanks to:
# https://djw8605.github.io/2016/05/03/building-centos-packages-on-travisci/
# https://github.com/opensciencegrid/htcondor-ce/tree/master/tests

# Version of CentOS/RHEL
el_version=$1
# need a varaible to point to the .travis directory
# Run tests in Container
if [ "$el_version" = "6" ]
then
    echo "Running SLC6 GEM DAQ custom docker image"
    docker_image=gitlab-registry.cern.ch/sturdy/gemdaq_ci_worker:slc6
    # docker_image=cern/slc6-base
    ls -lZ
    sudo docker run --rm=true -v `pwd`:/home/daqbuild/cmsgemos:rw --entrypoint="/bin/bash" \
         ${docker_image} -ec "echo Testing build on slc6;
  . /home/daqbuild/cmsgemos/.travis/docker.sh ${OS_VERSION};
  echo -ne \"------\nEND CMSGEMOS TESTS\n\";"
elif [ "$el_version" = "7" ]
then
    echo "Running CC7 GEM DAQ custom docker image"
    docker_image=gitlab-registry.cern.ch/sturdy/gemdaq_ci_worker:cc7
    # docker_image=cern/cc7-base
    ls -lZ
    docker run --privileged -d -ti -e "container=docker" -v /sys/fs/cgroup:/sys/fs/cgroup \
           -v `pwd`:/home/daqbuild/cmsgemos:rw $docker_image /usr/sbin/init
    DOCKER_CONTAINER_ID=$(docker ps | grep "gemdaq_ci_worker:cc7" | awk '{print $1}')
    docker logs $DOCKER_CONTAINER_ID
    docker exec -ti $DOCKER_CONTAINER_ID /bin/bash -ec "echo Testing build on cc7;
  . /home/daqbuild/cmsgemos/.travis/docker.sh ${OS_VERSION};
  echo -ne \"------\nEND CMSGEMOS TESTS\n\";"
    docker ps -a
    docker stop $DOCKER_CONTAINER_ID
    docker rm -v $DOCKER_CONTAINER_ID
elif [ "$el_version" = "8" ]
then
    echo "Running CC8 GEM DAQ custom docker image"
fi
