import pika
import argparse
import json
import time
from csv import DictWriter
import threading

# message = {
#     "measurement": "low_level_driver",
#     "time": timestamp,
#     "tags": {
#         "source": "low_level_driver"
#     },
#     "fields": {
#         "t1": readings[0],
#         "time_t1": timestamps[0],
#         "t2": readings[1],
#         "time_t2": timestamps[1],
#         "t3": readings[2],
#         "time_t3": timestamps[2],
#         "average_temperature": (readings[1] + readings[2]) / 2,
#         "heater_on": self.heater.is_lit,
#         "fan_on": self.fan.is_lit,
#         "execution_interval": exec_interval,
#         "elapsed": time.time() - start
#     }
# }
ROUTING_KEY_STATE = "incubator.record.driver.state"
ROUTING_KEY_CONTROLLER = "incubator.record.controller.state"
ROUTING_KEY_HEATER = "incubator.hardware.gpio.heater.on"
ROUTING_KEY_FAN = "incubator.hardware.gpio.fan.on"

def experiment1(rabbitmq_host, rabbitmq_port):
    fieldnames = ["time", "t1", "time_t1", "t2", "time_t2", "t3", "time_t3", "average_temperature", "heater_on",
                  "execution_interval", "elapsed"]
    defaults={ k:0 for k in fieldnames}

    with open("output.csv", "w") as file:
        writer = DictWriter(file, fieldnames=sorted(defaults.keys()))
        writer.writeheader()

        def callback(ch, method, properties, body):
            data = json.loads(body)

            time = {"time": data["time"]}
            fields = {attribute: value for attribute, value in data["fields"].items()}
            fields.update(time)
            kv=defaults.copy()
            kv.update(fields)

            writer.writerow(kv)



        credentials = pika.PlainCredentials("guest", "guest")
        parameters = pika.ConnectionParameters(rabbitmq_host, rabbitmq_port, '/', credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.exchange_declare(exchange="Incubator_AMQP", exchange_type="topic")
        result = channel.queue_declare(queue="observer",durable=False, auto_delete=True)
        channel.queue_bind(exchange="Incubator_AMQP", queue=result.method.queue, routing_key=ROUTING_KEY_STATE)

        channel.basic_consume(queue=result.method.queue,
                              auto_ack=True, exclusive=True,
                              on_message_callback=callback)


        def process():
            try:
                channel.start_consuming()
            except pika.exceptions.StreamLostError:
                pass
            except AssertionError:
                pass
            except ValueError:
                pass


        t=threading.Thread(target=process,
                         daemon=True)
        t.start()

        # ---------------- Experiment ----------------
        connection2 = pika.BlockingConnection(parameters)
        channel2 = connection2.channel()
        # record for 10s of current temp
        time.sleep(1)

        # heat on for 30s
        channel2.basic_publish(exchange="Incubator_AMQP", routing_key=ROUTING_KEY_HEATER,
                              body=json.dumps(True))
        time.sleep(3)
        channel2.basic_publish(exchange="Incubator_AMQP", routing_key=ROUTING_KEY_HEATER,
                              body=json.dumps(False))

        # record 5 min
        time.sleep(6 * 5)

        # ---------------- Experiment end-------------


if __name__ == '__main__':

    options = argparse.ArgumentParser(prog="profiler")

    options.add_argument("-ip", dest="ip", type=str, required=True)

    args = options.parse_args()


    experiment1(args.ip, 5672)
