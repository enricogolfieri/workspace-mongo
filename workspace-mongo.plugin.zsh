mongows=$HOME/.config/workspace-mongo
function mongo-dev-activate() 
{
    . $mongows/.profile.dev.zsh
}

function mongo-vm-activate()
{
    . $mongows/.profile.vm.zsh
}
