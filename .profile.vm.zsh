

source $mongows/.mongo-vm-functions

# JIRA Username
export JIRA_USERNAME=enrico.golfieri@mongodb.com
#ICECC cloud
if [[ -n $_is_arm_linux ]]; then
    export _icecc_cloud="iceccd-graviton.production.build.10gen.cc" #arm64
else
    export _icecc_cloud="iceccd.production.build.10gen.cc" #x86
fi

export PATH="/usr/local/sbin:/usr/sbin:/usr/bin:/bin:$PATH"
#add scripts
export PATH="$ctools_path":$PATH

### Set general environment settings
export LC_ALL="C"
export NINJA_STATUS="%p [%f/%t] (%r) %e"

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

if [ -d "/snap/bin" ]; then 
    export PATH="/snap/bin:$PATH"
fi

# MongoDB Toolchain
#This will also overwrite your local python3
if [ -d "/opt/mongodbtoolchain" ]; then
    export PATH="/opt/mongodbtoolchain/v4/bin:$PATH"
fi

#This will overwrite the mongodb toolchain clang
if [ -d "$HOME/llvm-project/build/bin/" ]; then
    export PATH="$HOME/llvm-project/build/bin/:$PATH"
fi

alias python=python3

