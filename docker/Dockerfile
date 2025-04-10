FROM ubuntu:22.04
RUN apt-get update && \
      apt-get -y install sudo

# Install dependencies
RUN apt install -y python3 git gdb vim libxml2-dev libssl-dev libcurl3-dev libkrb5-dev libsasl2-dev libldap-dev python3.10-venv wget curl build-essential

# Install zsh
RUN apt-get install -y zsh
RUN chsh -s $(which zsh) $(whoami)

# Install antigen
RUN curl -L git.io/antigen > ~/antigen.zsh

# Install rust
RUN apt install -y snapd gh xclip htop ncdu bpytop tmux nano xclip ripgrep
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Install mrlog 
RUN git clone https://github.com/markbenvenuto/mrlog.git /tmp/mrlog
RUN . $HOME/.cargo/env && \
    cargo install --path /tmp/mrlog && \
    cp $HOME/.cargo/bin/mrlog /usr/bin/
# Install fzf
RUN git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf && ~/.fzf/install --completion --key-bindings --no-update-rc

# Install nvm
RUN export _nvm_version=0.38.0 && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v$_nvm_version/install.sh | bash
RUN . ~/.nvm/nvm.sh && nvm install node --lts
# Install npm 
RUN bash -c 'source ~/.nvm/nvm.sh && \
    nvm install --lts && \
    nvm use --lts && \
    # Install latest npm within this environment
    npm install -g npm && \
    # Install m if you still need it
    npm install -g m && \
    # Create global symlinks so the installed node is available to all shells
    ln -sf $(which node) /usr/local/bin/node && \
    ln -sf $(which npm) /usr/local/bin/npm'

# Install toolchain
RUN curl -o /tmp/toolchain_installer.sh http://mongodbtoolchain.build.10gen.cc/installer.sh 
RUN chmod +x /tmp/toolchain_installer.sh
RUN USER=${USER:-$(whoami)} /tmp/toolchain_installer.sh

# Install pymongo
RUN /opt/mongodbtoolchain/v5/bin/pip3 install pymongo

# Install mongosh for aarch64
# NOTE check documentation to install it for a different architecture 
RUN sudo apt-get install gnupg && curl -fsSL https://pgp.mongodb.com/server-6.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor
RUN echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
RUN sudo apt-get update && sudo apt-get install -y mongodb-mongosh

# Install mongo tools (mongo export, mongosync etc ..)
# NOTE check documentation to install it for a different architecture 
RUN curl "https://fastdl.mongodb.org/tools/db/mongodb-database-tools-amazon2023-aarch64-100.9.5.tgz" --output /tmp/user-tools.tgz 
RUN mkdir -p /tmp/user-tools-output && tar -zxvf /tmp/user-tools.tgz -C /tmp/user-tools-output --strip-components=1 && cp /tmp/user-tools-output/bin/* /usr/local/bin/

# Install evergreen for aarch64
# NOTE check evergreen website to install it for a different architecture 
RUN curl https://evg-bucket-evergreen.s3.amazonaws.com/evergreen/clients/evergreen_ad3a8afd665f67cb48b4742b6514230d8a519a60/linux_arm64/evergreen -o /tmp/evergreen
RUN mv /tmp/evergreen /usr/local/bin/evergreen && sudo chmod +x /usr/local/bin/evergreen

# install workspace 
RUN git clone https://github.com/enricogolfieri/workspace.git /root/.workspace