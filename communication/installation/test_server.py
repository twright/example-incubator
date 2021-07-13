import logging
import time

from communication.server.rabbitmq import Rabbitmq
from config.config import config_logger, load_config

if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)

    config_logger("logging.conf")
    config = load_config("startup.conf")

    receiver = Rabbitmq(**config)
    receiver.connect_to_server()
    qname = receiver.declare_local_queue(routing_key="test")

    sender = Rabbitmq(**config)
    sender.connect_to_server()
    sender.send_message(routing_key="test", message={"text": "321"})

    time.sleep(0.01)  # in case too fast that the message has not been delivered.

    msg = receiver.get_message(queue_name=qname)
    print("received message is", msg)

