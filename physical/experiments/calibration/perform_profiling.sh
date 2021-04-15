#!/bin/bash

# make sure that the project is build prior to this e.g.
# in the incubator folder run (make sure the build tool is installed as well pipenv run python -m pip install --upgrade build)
# pipenv run python -m build

initialize_target(){

docker build  -t platform_profiling .
 # start docker since we dont have the remote yet
docker run -d --rm -p $target_ssh_port:22 --name test_sshd platform_profiling
#docker exec test_sshd touch /root/.ssh/authorized_keys
cat  ~/.ssh/id_rsa.pub >> authorized_keys
docker cp  authorized_keys test_sshd:/root/.ssh/authorized_keys
#docker exec test_sshd cat /root/.ssh/authorized_keys/id_rsa.pub >> /root/.ssh/authorized_keys && rm /root/.ssh/authorized_keys/id_rsa.pub

docker exec test_sshd chown root:root /root/.ssh/authorized_keys

echo Host up

}

deinitialize_target(){

docker stop test_sshd
}
############################ SETUP ####################################

profiling_script=profiling.py

target_ssh_host=localhost
target_ssh_port=5022
target_ssh_user=root
target_driver_whl=../incubator/dist/incubator-1.0.0-py3-none-any.whl
target_dest=/tmp/hardware_profiling
target_script="from physical_twin import low_level_driver_server\nlow_level_driver_server.main()"
target_conf='rabbitmq: {\n
\tip = "10.17.98.239"\n
\tport = 5672\n
\tusername = incubator\n
\tpassword = incubator\n
\texchange = Incubator_AMQP\n
\ttype = topic\n
\tvhost = /\n
}'

echo $target_conf



############################ DEPLOY REMOTE ############################
initialize_target


ssh $target_ssh_user@$target_ssh_host -p $target_ssh_port /bin/bash << EOF

echo "Clean up"
rm -rf $target_dest
mkdir -p $target_dest
cd $target_dest
pipenv install
EOF

echo Host configured

# make and copy files to target
echo -e $target_script > script.py
echo -e $target_conf > startup.conf
scp -P $target_ssh_port $target_driver_whl script.py startup.conf $target_ssh_user@$target_ssh_host:$target_dest
rm script.py startup.conf

echo Upload complated

# start the remote client
whl_file="$(basename -- $target_driver_whl)"
ssh $target_ssh_user@$target_ssh_host -p $target_ssh_port /bin/bash << EOF

cd $target_dest
pipenv install $whl_file
cat script.py

pipenv run python script.py --conf startup.conf

EOF


############################ Start profiling job ############################

pipenv run python profiling_script.py


deinitialize_target