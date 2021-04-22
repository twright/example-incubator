
from testcontainers.core.container import DockerContainer
from physical.experiments.heater_and_heat_disipation_profiling.raspberry_pi.HeatingElementProfilingExperiment import HeatingElementProfilingExperiment
import os
import paramiko


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


class HeatingElementProfilingExperimentDummyTarget(HeatingElementProfilingExperiment):


    target_service = TargetAsService()

    def get_services(self):
        return [self.rabbitmq_service, self.target_service]

    def get_service_host_hostname(self):
        import socket
        return socket.gethostbyname(socket.gethostname())

    def get_ssh_client(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.target_service.get_container_host_ip(), self.target_service.get_exposed_port(22), "root", "root")
        return client


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
        print(alternate_script)
        stdin, stdout, stderr = ssh.exec_command(
            'echo -e "' + alternate_script + '" >/tmp/work/script.py')
        self.verbose(stdout)
        self.verbose(stderr)

    def describe(self):
        return '''Generate a profile of the heating element by switching it on and off over time. This just returns dummy data.'''


if __name__ == '__main__':
     HeatingElementProfilingExperimentDummyTarget().run()