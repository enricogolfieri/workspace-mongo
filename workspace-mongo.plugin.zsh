mongows=$(dirname "${(%):-%x}")

mongo-enable() {
    source $mongows/.profile.vm.zsh
    source $mongows/.profile.dev.zsh
}

function mongo-setup-env()
{
    # Download mongo repo if not present
    if [ ! -d $HOME/mongo ]; then
        git clone git@github.com:10gen/mongo $HOME/mongo
    else 
        echo "mongo repo already exists, skipping download"
    fi
    # Download sls repo if not present 
    if [ ! -d $HOME/sls ]; then
        git clone git@github.com:10gen/sls $HOME/sls
    else 
        echo "sls repo already exists, skipping download"
    fi
    mkdir -p $HOME/.cursor/skills
    ln -sf $mongows/cursor/skills/mongo-dev $HOME/.cursor/skills/mongo-dev 
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

