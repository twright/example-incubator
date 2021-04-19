FROM rastasheep/ubuntu-sshd

RUN export DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true && \
apt-get update &&\
apt install software-properties-common tzdata curl -y &&\
dpkg-reconfigure --frontend noninteractive tzdata&&\
add-apt-repository ppa:deadsnakes/ppa -y&&\
apt-get update&&\
apt-get --yes install python3.9  python3.9-distutils&&\
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py&&\
python3.9 get-pip.py&&\
pip3 install  pipenv


EXPOSE 22