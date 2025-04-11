mongows=$(dirname "${(%):-%x}")

mongo-enable() {
    source $mongows/.profile.vm.zsh
    source $mongows/.profile.dev.zsh
}

function mongo-build-docker()
{
    docker-compose -f $mongows/docker/docker-compose.mongo.yml up -d --build dev-mongo
}

function mongo-run-docker()
{
    docker-compose -f $mongows/docker/docker-compose.mongo.yml up -d
}

function mongo-stop-docker()
{
    docker-compose -f $mongows/docker/docker-compose.mongo.yml down
}

#attach to mongo container
function mongo-attach()
{
    docker exec -it dev-mongo-1 zsh
}
