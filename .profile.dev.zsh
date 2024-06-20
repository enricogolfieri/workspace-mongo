#add mongofunction
source $mongows/.mongo-dev-functions
source $mongows/.mongo-evg-functions
source $mongows/.mongo-help-functions

# Env variables
export PATH="$mongows/bashscripts:$PATH"
_mongo_tools="$HOME/mongo-tools"
_ctool_path="$_mongo_tools"/ctools

### Compute _os variable
_os="Linux";

case `uname` in
    Darwin)
        _os="Darwin"
        _is_macos=1
    ;;
    Linux)
        _os="Linux"
        _is_linux=1
    ;;
    *)
        echo "[WORKSPACE-MONGO-DEV] Unsupported OS, impossible to setup"
        return 1            
    ;;
esac

if [[ $(uname -m) == 'arm64' ]]; then
  _is_arm=1
  [ -n $_is_linux ] && _is_arm_linux=1
fi

export NINJA_STATUS='[%f/%t (%p) %es] '

#Do not print in case of non-interactive shell
[[ $- == *i* ]] || return

echo "mongo environment activated for $_os"

