mongows=$(dirname "${(%):-%x}")
function mongo-dev-activate() 
{
    . $mongows/.profile.dev.zsh
}

function mongo-vm-activate()
{
    . $mongows/.profile.vm.zsh
}
