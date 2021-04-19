from testcontainers.core.container import DockerContainer
import socket
from Experiments import OnTargetExperiment
from python_profiling_script import experiment1
from testcontainer_python_rabbitmq import RabbitMQContainer
import os
import paramiko
from scp import SCPClient
from pathlib import Path


# class RabbitmqService:
#     def get_host_name(self):
#         return socket.gethostbyname(socket.gethostname())
#
#     def get_port(self):
#         return 5672
#
#     def __enter__(self):
#         start_docker_rabbitmq()
#
#     def __exit__(self, type, value, traceback):
#         stop_docker_rabbitmq()

class DockerContainerFromDockerfile(DockerContainer):
    '''Utilitty class to make a docker contain service from a docker file'''
    from testcontainers.core.utils import setup_logger
    logger = setup_logger(__name__)

    def __init__(self, path):
        super().__init__(image="")
        self.path = path

    def start(self):
        self.logger.info("Building image %s", self.path)
        image, generator = self.get_docker_client().client.images.build(dockerfile="Dockerfile", path=self.path)
        self.image = image
        return super().start()


class TargetAsService(DockerContainerFromDockerfile):
    '''Docker container from the docker file in the same directory as this file'''
    from testcontainers.core.utils import setup_logger
    logger = setup_logger(__name__)

    def __init__(self):
        super().__init__(os.path.dirname(__file__))
        self.with_exposed_ports(22)


class HeatingElementProfilingExperiment(OnTargetExperiment):
    rabbitmq_service = RabbitMQContainer()
    target_service = TargetAsService()

    def get_services(self):
        return [self.rabbitmq_service, self.target_service]

    def get_rabbitmq_conf(self):
        return '''rabbitmq: {
    ip = "''' + self.get_service_host_hostname() + ''''"
    port = ''' + str(self.rabbitmq_service.get_amqp_port()) + '''
    username = guest
    password = guest
    exchange = Incubator_AMQP
    type = topic
    vhost = /
}
            '''

    def configure_target(self):
        wd = self.get_working_dir()
        with open(wd / "rabbitmq.conf", 'w') as f:
            f.write(self.get_rabbitmq_conf())

    def configure_local(self):
        pass

    def createSSHClient(self,server, port, user, password):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server, port, user, password)
        return client

    def setup_target(self):
        ssh = self.createSSHClient(self.target_service.get_container_host_ip(),
                                   self.target_service.get_exposed_port(22), "root", "root")
        scp = SCPClient(ssh.get_transport())
        this_file: Path = Path(os.path.dirname(__file__))
        dist = this_file.parent.parent.parent / 'dist'
        whls = [f for f in dist.iterdir() if f.name.endswith(".whl")]
        if len(whls) == 0:
            raise "No why found please build package first"
        stdin, stdout, stderr = ssh.exec_command('mkdir -p /tmp/work')
        self.verbose(stdout)
        self.verbose(stderr)
        scp.put(whls[0], "/tmp/work")
        scp.put(self.get_working_dir()/"rabbitmq.conf", "/tmp/work")
        stdin, stdout, stderr = ssh.exec_command('cd /tmp/work && pipenv install '+Path(whls[0]).name)
        self.verbose(stdout)
        self.verbose(stderr)

        stdin, stdout, stderr = ssh.exec_command('echo -e "from physical_twin import low_level_driver_server\nlow_level_driver_server.main()" >/tmp/work/script.py')
        self.verbose(stdout)
        self.verbose(stderr)

        stdin, stdout, stderr = ssh.exec_command(
            'echo -e "from physical_twin import low_level_driver_server\nlow_level_driver_server.main()" >/tmp/work/script.py')
        self.verbose(stdout)
        self.verbose(stderr)


    def verbose(self,stream):
        for s in stream:
            print(s)

    def teardown_target(self):
        pass

    def do_local_experiment(self):
        experiment1(self.get_service_host_hostname(), self.rabbitmq_service.get_amqp_port())

    def do_target_experiment(self):
        ssh = self.createSSHClient(self.target_service.get_container_host_ip(),
                                   self.target_service.get_exposed_port(22), "root", "root")
        stdin, stdout, stderr = ssh.exec_command('cd /tmp/work && pipenv run python script.py --conf rabbitmq.conf')
        self.verbose(stdout)
        self.verbose(stderr)

    def describe(self):
        return '''Generate a profile of the heating element by switching it on and off over time'''

class HeatingElementProfilingExperimentDummyTarget(HeatingElementProfilingExperiment):
    def setup_target(self):
        super().setup_target()
        ssh = self.createSSHClient(self.target_service.get_container_host_ip(),
                                   self.target_service.get_exposed_port(22), "root", "root")

        alternate_script = '''import pika
import random
import time
import json

credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters( ''' + "'" + self.get_service_host_hostname() + "'" + ''' ,
                                                   ''' + str(self.rabbitmq_service.get_amqp_port()) + ''',
                                                   '/',
                                                   credentials)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange='Incubator_AMQP', exchange_type='topic')
try:
    while True:
        data={'time':time.time_ns(),'fields':{'t1':random.uniform(1.5, 1.9),'t2':random.uniform(1.5, 1.9),'t3':random.uniform(1.5, 1.9)}}     
        if channel.is_open:   
            channel.basic_publish(exchange='Incubator_AMQP', routing_key='incubator.record.driver.state', body=json.dumps(data))        
except pika.exceptions.StreamLostError:
    pass
'''
        # print(alternate_script)
        stdin, stdout, stderr = ssh.exec_command(
            'echo -e "' + alternate_script + '" >/tmp/work/script.py')
        self.verbose(stdout)
        self.verbose(stderr)

    def describe(self):
        return '''Generate a profile of the heating element by switching it on and off over time. This just returns dummy data.'''

if __name__ == '__main__':
    # with TargetAsService() as target_service:
    #     client = paramiko.SSHClient()
    #     client.load_system_host_keys()
    #     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #     client.connect(hostname=target_service.get_container_host_ip(),
    #                    port=target_service.get_exposed_port(22), username="root", password="root")
    #     stdin, stdout, stderr = client.exec_command('ls -la')
    #     for s in stdout:
    #         print(s)
    HeatingElementProfilingExperimentDummyTarget().run()
