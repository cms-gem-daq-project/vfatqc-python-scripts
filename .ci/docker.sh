#!/bin/bash -xe

# Thanks to:
# https://djw8605.github.io/2016/05/03/building-centos-packages-on-travisci/
# https://github.com/opensciencegrid/htcondor-ce/tree/master/tests

# Version of CentOS/RHEL
COMMAND=$1
DOCKER_IMAGE=$2
OS_VERSION=$3
REPO_NAME=${TRAVIS_REPO_SLUG#?*/}

# need a varaible to point to the .ci directory
# Run tests in Container
if [ "${COMMAND}" = "setup" ]
then
    echo "Setting up system for docker image"
    sudo apt-get update
    sudo usermod -aG docker $USER
    sudo groupadd daqbuild -g 2055
    sudo useradd daqbuild -g 2055 -u 2055
    sudo usermod -aG daqbuild $USER
    groups
    sudo chmod g+s -R $HOME
    sudo apt-get install acl acl2
    sudo setfacl -Rdm u::rwX,g::rwX,o::rX $HOME
    sudo setfacl -Rm  u::rwX,g::rwX,o::rX $HOME

    echo 'DOCKER_OPTS="-H tcp://127.0.0.1:2375 -H unix:///var/run/docker.sock -s devicemapper"' | \
        sudo tee /etc/default/docker > /dev/null
    sudo service docker restart
    docker pull ${DOCKER_IMAGE}
    docker ps -al
    sudo chown :daqbuild -R .
elif [ "${COMMAND}" = "start" ]
then
    if [[ "${DOCKER_IMAGE}" =~ slc6$ ]]
    then
        echo "Starting SLC6 GEM DAQ custom docker image"
        docker run --user daqbuild --privileged=true -d -ti -e "container=docker" \
               -v `pwd`:/home/daqbuild/${REPO_NAME}:rw,z \
               ${DOCKER_IMAGE} /bin/bash
    elif [[ "${DOCKER_IMAGE}" =~ cc7$ ]]
    then
        echo "Starting CC7 GEM DAQ custom docker image"
        docker run --user daqbuild --privileged=true -d -ti -e "container=docker" \
               -v /sys/fs/cgroup:/sys/fs/cgroup \
               -v `pwd`:/home/daqbuild/${REPO_NAME}:rw,z \
               ${DOCKER_IMAGE} /usr/sbin/init
    elif [[ "${DOCKER_IMAGE}" =~ cc8$ ]]
    then
        echo "Starting CC8 GEM DAQ custom docker image"
    else
        echo "Unknown docker image specified"
        exit 1
    fi

    DOCKER_CONTAINER_ID=$(docker ps | grep ${DOCKER_IMAGE} | awk '{print $1}')
    echo DOCKER_CONTAINER_ID=${DOCKER_CONTAINER_ID}
    if [ ! -z ${DOCKER_CONTAINER_ID+x} ];
    then
        docker exec -ti ${DOCKER_CONTAINER_ID} /bin/bash -ec 'echo Testing build on docker for `cat /etc/system-release`'
        docker logs $DOCKER_CONTAINER_ID
        docker exec -ti ${DOCKER_CONTAINER_ID} /bin/bash -ec 'pip install -I --user "pip" "importlib" "codecov" "setuptools<38.2"'
        docker exec -ti ${DOCKER_CONTAINER_ID} /bin/bash -ec 'python -c "import pkg_resources; print(pkg_resources.get_distribution('\''importlib'\''))"'
        docker exec -ti ${DOCKER_CONTAINER_ID} /bin/bash -ec 'python -c "import pkg_resources; print(pkg_resources.get_distribution('\''pip'\''))"'
        docker exec -ti ${DOCKER_CONTAINER_ID} /bin/bash -ec 'python -c "import pkg_resources; print(pkg_resources.get_distribution('\''setuptools'\''))"'
    fi
else
    DOCKER_CONTAINER_ID=$(docker ps | grep ${DOCKER_IMAGE} | awk '{print $1}')
    if [ ! -z ${DOCKER_CONTAINER_ID+x} ];
    then
        docker logs $DOCKER_CONTAINER_ID

        if [ "${COMMAND}" = "stop" ]
        then
            docker exec -ti ${DOCKER_CONTAINER_ID} /bin/bash -ec "echo -ne \"------\nEND ${REPO_NAME} TESTS\n\";"
            docker stop $DOCKER_CONTAINER_ID
            docker rm -v $DOCKER_CONTAINER_ID
        elif [ "${COMMAND}" = "other" ]
        then
            docker ps -a
        fi
    fi
fi

docker ps -a

exit 0
