import logging
import time

from communication.server.rabbitmq import Rabbitmq

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    
    rabbbitmq_config = {
        "ip": "localhost",
        "port": 5672,
        "username": "incubator",
        "password": "incubator",
        "exchange": "Incubator_AMQP",
        "type": "topic",
        "vhost": "/"
    }

    receiver = Rabbitmq(**rabbbitmq_config)
    receiver.connect_to_server()
    qname = receiver.declare_local_queue(routing_key="test")

    sender = Rabbitmq(**rabbbitmq_config)
    sender.connect_to_server()
    sender.send_message(routing_key="test", message={"text": "321"})

    time.sleep(0.01)  # in case too fast that the message has not been delivered.

    msg = receiver.get_message(queue_name=qname)
    print("received message is", msg)

