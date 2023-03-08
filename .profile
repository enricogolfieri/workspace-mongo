#add mongofunction

export NINJA_STATUS='[%f/%t (%p) %es] '

#add scripts
export PATH="$wsmdb_path"/bashscripts:$PATH
export PATH="$ctools_path":$PATH

[[ $- == *i* ]] || return

echo "mongo environment activated for $_os"
