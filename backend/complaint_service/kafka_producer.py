import os
import json
from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER")

# Pipeline Topics
TOPIC_SUBMITTED = os.getenv("TOPIC_COMPLAINT_SUBMITTED")
TOPIC_CATEGORIZED = os.getenv("TOPIC_COMPLAINT_CATEGORIZED")
TOPIC_STATUS_UPDATED = os.getenv("TOPIC_COMPLAINT_STATUS_UPDATED")

producer = None


def get_producer():
    global producer

    if producer is None:
        print(f"Connecting to Kafka at {KAFKA_BROKER}...")

        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=3,
                request_timeout_ms=10000
            )
            print("Kafka producer connected.")
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}")
            raise

    return producer


def send_event(topic, event):
    """Send an event to a specific Kafka topic."""
    try:
        producer_instance = get_producer()
        producer_instance.send(topic, event)
        producer_instance.flush()
        print(f"Event sent to topic: {topic}")
    except Exception as e:
        print(f"Failed to send event to {topic}: {e}")
        raise


def send_complaint_submitted(event):
    """Publish when a new complaint is submitted."""
    send_event(TOPIC_SUBMITTED, event)


def send_complaint_categorized(event):
    """Publish after ML categorization."""
    send_event(TOPIC_CATEGORIZED, event)


def send_status_update(event):
    """Publish when complaint status changes."""
    send_event(TOPIC_STATUS_UPDATED, event)