#add mongofunction

export NINJA_STATUS='[%f/%t (%p) %es] '

export PATH="/usr/local/sbin:/usr/sbin:/usr/bin:/bin:$PATH"
#add scripts
export PATH="$wsmdb_path"/bashscripts:$PATH
export PATH="$ctools_path":$PATH

### Set general environment settings
export LC_ALL="C"

if [ -d /opt/go ]; then
    export PATH=/opt/go/bin:$PATH
    export GOROOT=/opt/go
fi

if [ -d "$HOME/cli_bin" ]; then
    export PATH="$HOME/cli_bin:$PATH"
fi

if [ -d "/opt/undodb5/bin" ]; then
    export PATH="/opt/undodb5/bin:$PATH"
fi

if [ -d "/opt/rtags-2.38/bin" ]; then
    export PATH="/opt/rtags-2.38/bin:$PATH"
fi

if [ -d "/opt/node/bin" ]; then
    export PATH="/opt/node/bin:$PATH"
fi

if [ -d "$HOME/.local/bin" ]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

#This will also overwrite your local python3
if [ -d "/opt/mongodbtoolchain" ]; then
    export PATH="/opt/mongodbtoolchain/v4/bin:$PATH"
fi

# MongoDB Toolchain
[[ $- == *i* ]] || return

echo "mongo environment activated for $_os"

