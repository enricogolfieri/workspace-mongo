
WS_PATH=$HOME/.workspace
WS_PLUGINS_PATH=$WS_PATH/plugins
function load()
{
    ANTIGEN_LOG=/tmp/antigen.log
    source ~/antigen.zsh
    # Load the oh-my-zsh's library.
    antigen use oh-my-zsh

    # Bundles from the default repo (robbyrussell's oh-my-zsh).
    antigen bundle heroku
    antigen bundle fzf
    antigen bundle zsh-users/zsh-autosuggestions
    antigen bundle zsh-users/zsh-completions
    antigen bundle zsh-users/zsh-history-substring-search
    antigen bundle zsh-users/zsh-syntax-highlighting
    antigen bundle hschne/fzf-git

    # Nvm
    export NVM_DIR="$HOME/.nvm"
    export NVM_LAZY_LOAD=true
    export NVM_COMPLETION=true
    antigen bundle lukechilds/zsh-nvm

    # Syntax highlighting bundle.
    antigen bundle zsh-users/zsh-syntax-highlighting

    #theme
    antigen theme https://github.com/romkatv/powerlevel10k.git
    antigen bundle enricogolfieri/p10k-config --branch=main

    # Load mongo
    antigen bundle enricogolfieri/workspace-mongo --branch=main

    # Load venv 
    antigen bundle enricogolfieri/antigen-venv.git --branch=main

    # Tell Antigen that you're done.
    antigen apply

    #Always activate mongo environment
    mongo-enable

    #Set-up history
    HISTFILE=~/.zsh_history
    HISTSIZE=100000
    SAVEHIST=100000
    setopt SHARE_HISTORY
    unsetopt HIST_IGNORE_SPACE

    # For disagg
    CARGO_HOME="/root/.ds_toolchain/.cargo"
    RUSTUP_HOME="/root/.ds_toolchain/.rustup"
    PATH="/root/.ds_toolchain/coveralls/bin:/root/.ds_toolchain/yq/bin:/root/.ds_toolchain/jq/bin:/root/.ds_toolchain/buf/bin:/root/.ds_toolchain/helm/bin:/root/.ds_toolchain/minikube/bin:/root/.ds_toolchain/mongosh/bin:/root/.ds_toolchain/grpcurl/bin:/root/.ds_toolchain/sccache/bin:/root/.ds_toolchain/protoc/bin:/root/.ds_toolchain/just/bin:/root/.ds_toolchain/.cargo/bin:$PATH"

    ### Set aliases
    alias ls='ls -h --color=auto'
    alias ll='ls -l'
    alias la='ls -la'
    alias rm='rm -i'
    alias grep='grep --color=always'
    alias more='more --RAW-CONTROL-CHARS --chop-long-lines'
    alias less='less --RAW-CONTROL-CHARS --chop-long-lines --IGNORE-CASE'
}

function load-w-trace()
{
    zmodload zsh/zprof  
    load
    zprof
}

load
