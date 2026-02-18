import json
from kafka import KafkaProducer

TOPIC = "complaints_topic"

producer = None


def get_producer():
    global producer

    if producer is None:
        print("Connecting to Kafka...")

        producer = KafkaProducer(
            bootstrap_servers="localhost:9092",
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )

        print("Kafka producer connected.")

    return producer


def send_complaint_event(event):

    producer_instance = get_producer()

    producer_instance.send(TOPIC, event)
    producer_instance.flush()

    print("Event sent to Kafka.")