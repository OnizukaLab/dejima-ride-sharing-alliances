#!/usr/bin/bash

command_name=$1

function start(){
    cd ${1}
    docker-compose up
}

function remove(){
    # alliance
    dockers=$(docker ps -a | grep "alliance" | awk '{print $1}')
    if [ "$dockers" == "" ]; then
        echo "no alliance dockers found"
        return
    fi
    echo $dockers | xargs docker rm -fv
    echo "removed alliance dockers"
    
    # provider
    dockers=$(docker ps -a | grep "provider" | awk '{print $1}')
    if [ "$dockers" == "" ]; then
        echo "no provider dockers found"
        return
    fi
    echo $dockers | xargs docker rm -fv
    echo "removed provider dockers"
}

function update(){
    cp -r "./proxy" "./env_generator/src/RSAB/"
    peer_dirs=$(find ./env_generator/RSAB* -maxdepth 0)
    for peer_dir in $peer_dirs; do
        cp "${peer_dir}/proxy/dejima_config.json" "${peer_dir}/dejima_config.json"
        cp -r "./proxy" $peer_dir
        mv "${peer_dir}/dejima_config.json" "${peer_dir}/proxy/dejima_config.json"
    done
    echo "updated RSAB files"
}

if [ $command_name == "start" ]; then
    remove
    update
    start $2
elif [ $command_name == "remove" ]; then
    remove
    update
elif [ $command_name == "update" ]; then
    update
fi