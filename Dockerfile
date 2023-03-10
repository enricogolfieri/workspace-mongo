FROM ubuntu:18.04
RUN apt-get update && apt-get install -y git curl build-essential sudo

RUN /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

RUN eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
ENV PATH="/home/linuxbrew/.linuxbrew/bin:${PATH}"
    
#install utils
RUN brew install rust gh fzf 
RUN brew install node
RUN brew install python@3.10
RUN brew install ninja ccache llvm
RUN brew cleanup
ENV PATH="/home/linuxbrew/.linuxbrew/opt/python:${PATH}"

#install utilities

#install mark benvenuto mrlog (since it takes some time)
ENV MONGOTOOLS="/root/mongo-tools"

RUN git clone https://github.com/markbenvenuto/mrlog.git ${MONGOTOOLS}/mrlog && \
        cd ${MONGOTOOLS}/mrlog && \
        cargo install --path .
ENV PATH="/root/.cargo/bin:${PATH}"

# write utilities to bashrc
RUN echo "alias load='source $HOME/.config/workspace-mongo/.aliases && mongo-activate';" >> /root/.bashrc
USER root
ENV USER root
