mongows=$(dirname "${(%):-%x}")

mongo-enable() {
    source $mongows/.profile.vm.zsh
    source $mongows/.profile.dev.zsh
}

function mongo-install-skills()
{
    local installer="$mongows/install.sh"
    if [ ! -f "$installer" ]; then
        echo "install.sh not found at $installer"
        return 1
    fi
    bash "$installer" "$@"
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
    mongo-install-skills --target cursor
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

