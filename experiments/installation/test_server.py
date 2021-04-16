import logging
import time

from software.src.shared.communication import Rabbitmq

if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)

    receiver = Rabbitmq(ip="localhost")
    receiver.connect_to_server()
    qname = receiver.declare_local_queue(routing_key="tests")

    sender = Rabbitmq(ip="localhost")
    sender.connect_to_server()
    sender.send_message(routing_key="tests", message={"text": "321"})

    time.sleep(0.01)  # in case too fast that the message has not been delivered.

    msg = receiver.get_message(queue_name=qname)
    print("received message is", msg)

