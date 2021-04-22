from testcontainers.core.container import DockerContainer
import socket
from Experiments import OnTargetExperiment
from physical.experiments.heater_and_heat_disipation_profiling.python_profiling_script import experiment1
from testcontainer_python_rabbitmq import RabbitMQContainer
import os
import paramiko
from scp import SCPClient
from pathlib import Path


class HeatingElementProfilingExperiment(OnTargetExperiment):
    rabbitmq_service = RabbitMQContainer()

    def get_services(self):
        '''Define the services required for the experiment'''
        return [self.rabbitmq_service]

    def get_target_ip(self):
        ip = os.getenv('INCUBATOR_PI_IP')
        if ip is None:
            raise Exception("Missing env INCUBATOR_PI_IP")
        else:
            return ip

    def get_service_host_hostname(self):
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((self.get_target_ip(), 22))
        ip = s.getsockname()[0]
        return ip

    def get_rabbitmq_conf(self):
        return '''rabbitmq: {
    ip = "''' + self.get_service_host_hostname() + '''"
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

    def createSSHClient(self, server, port, user, password):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server, port, user, password)
        return client

    def get_ssh_client(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.get_target_ip(), 22, "pi")
        return client

    def setup_target(self):
        ssh = self.get_ssh_client()
        scp = SCPClient(ssh.get_transport())
        this_file: Path = Path(os.path.dirname(__file__))
        dist = this_file.parent.parent.parent.parent / 'dist'
        whls = [f for f in dist.iterdir() if f.name.endswith(".whl")]
        if len(whls) == 0:
            raise "No why found please build package first"
        stdin, stdout, stderr = ssh.exec_command('mkdir -p /tmp/work')
        self.verbose(stdout)
        self.verbose(stderr)
        scp.put(whls[0], "/tmp/work")
        scp.put(self.get_working_dir() / "rabbitmq.conf", "/tmp/work")

        stdin, stdout, stderr = ssh.exec_command(
            'cd /tmp/work && pipenv --rm  ; rm Pipfile*; pipenv install --three ' + Path(whls[0]).name, get_pty=True)
        self.verbose(stdout)
        self.verbose(stderr)

        stdin, stdout, stderr = ssh.exec_command(
            'echo -e "from physical_twin import low_level_driver_server\nlow_level_driver_server.main()" >/tmp/work/script.py')
        self.verbose(stdout)
        self.verbose(stderr)

    def verbose(self, stream):
        for s in stream:
            print(s)

    def teardown_target(self):
        pass

    def do_local_experiment(self):
        experiment1(self.get_result_dir(), self.get_service_host_hostname(), self.rabbitmq_service.get_amqp_port())

    def do_target_experiment(self):
        ssh = ssh = self.get_ssh_client()
        stdin, stdout, stderr = ssh.exec_command('cd /tmp/work && pipenv run python script.py --conf rabbitmq.conf')
        self.verbose(stdout)
        self.verbose(stderr)

    def describe(self):
        return '''Generate a profile of the heating element by switching it on and off over time'''


if __name__ == '__main__':
    HeatingElementProfilingExperiment().run()
