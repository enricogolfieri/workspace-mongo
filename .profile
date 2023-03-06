#add mongofunction

export NINJA_STATUS='[%f/%t (%p) %es] '

#add scripts
export PATH=~/.config/workspace/envs/mongo/bashscripts:$PATH

[[ $- == *i* ]] || return

echo "mongo environment activated for $_os"
