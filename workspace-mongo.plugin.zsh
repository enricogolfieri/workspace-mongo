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
    # Start with base command
    local cmd="docker-compose -f $mongows/docker/docker-compose.mongo.yml"
  
    # Add volumes as needed
    if [ -n "${WORKSPACE_VOLUME}" ]; then
        cmd="${cmd} -e WORKSPACE_VOLUME=${WORKSPACE_VOLUME}"
    fi

    if [ -n "${GITIGNORE_VOLUME}" ]; then
        cmd="${cmd} -e GITIGNORE_VOLUME=${GITIGNORE_VOLUME}"
    fi

    if [ -n "${GITCONFIG_VOLUME}" ]; then
        cmd="${cmd} -e GITCONFIG_VOLUME=${GITCONFIG_VOLUME}"
    fi

    if [ -n "${ZSHRC_VOLUME}" ]; then
        cmd="${cmd} -e ZSHRC_VOLUME=${ZSHRC_VOLUME}"
    fi

    if [ -n "${ZSHENV_VOLUME}" ]; then
        cmd="${cmd} -e ZSHENV_VOLUME=${ZSHENV_VOLUME}"
    fi

    # Execute the command with any additional arguments
    eval "${cmd} $@"
}
