## BashScript 
any bash script inside this folder is added to your path

# Local Machine
`git clone git@github.com:enricogolfieri/workspace $HOME/.config/workspace-mongo`
`echo 'source $HOME/.config/workspace-mongo/.aliases >> $HOME/.bashrc`

Local compilation on macos or linux:
    1. on macos install xcode 
    2. type `mongo-activate` for every shell to enable the environment
    3. install utilities tool `mongo-setup-tools`

Note: when you build locally, you will use the version of ninja, ccache, gcc, python etc installed in your system. There is no guarantee this will actually work.
You can still install the toolchain by running mongo-setup-toolchain but I would not recommend it.

# Virtual Machine AWS
`git clone git@github.com:enricogolfieri/workspace $HOME/.config/workspace-mongo`
`echo 'source $HOME/.config/workspace-mongo/.aliases && mongo-activate >> $HOME/.bashrc`
Compilation on a mongodb virtual machine:
    1. include to .bashrc `source $HOME/.config/workspace/mongovm/.bashrc`
    2. install mongo utilities `mongo-setup-tools`
    3. install or update mongo toolchain `mongo-setup-toolchain`

# Features:
mongo-prepare <version>: prepare the environment for the project (note this will store the version in the config file and will be used for any command until you run another mongo-prepare or mongo-configure)
mongo-configure <version>: configure the project (note this will store the version in the config file and will be used for any command until you run another mongo-prepare or mongo-configure)
mongo-build: build the project 
mongo-test-locally <jstests/path/to/js_test.js>
mongo-test-remotely : run the tests on evergreen
mongo-new-branch <branch_name> <branch_description> : create a new branch and store the description in the config file. This will be handy when you run mongo-test-remotely to automatically set the description of the patch

todo: finish the readme
