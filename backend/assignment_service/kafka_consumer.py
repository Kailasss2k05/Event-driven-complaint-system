import os
import json
from dotenv import load_dotenv
from kafka import KafkaConsumer, KafkaProducer

load_dotenv()

# Add project root to path for DB imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.db.database import update_complaint_assigned, insert_event

KAFKA_BROKER = os.getenv("KAFKA_BROKER")
TOPIC_CATEGORIZED = os.getenv("TOPIC_COMPLAINT_CATEGORIZED")
TOPIC_ASSIGNED = os.getenv("TOPIC_COMPLAINT_ASSIGNED")


def create_consumer():
    return KafkaConsumer(
        TOPIC_CATEGORIZED,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="assignment-group"
    )


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )


def process_event(event, producer):
    """Process a categorized complaint and assign it."""
    print("\nReceived Categorized Complaint:")
    print(event)

    complaint_id = event.get("complaint_id", "unknown")
    department = event.get("department", "Unassigned")
    priority = event.get("priority", "Normal")
    category = event.get("category", "Unknown")

    print(f"Complaint {complaint_id} -> Assigned to: {department} "
          f"(Category: {category}, Priority: {priority})")

    # Update database
    try:
        update_complaint_assigned(complaint_id, department)
        print(f"Database updated: complaint {complaint_id} assigned to {department}")
    except Exception as e:
        print(f"Warning: Failed to update DB: {e}")

    # Publish to complaint-assigned
    assigned_event = {
        **event,
        "status": "ASSIGNED",
        "assigned_to": department
    }

    producer.send(TOPIC_ASSIGNED, assigned_event)
    producer.flush()
    print(f"Assignment event published to {TOPIC_ASSIGNED}")

    # Note: Audit service will log this event from Kafka


def main():
    print(f"Assignment Service connecting to Kafka at {KAFKA_BROKER}...")
    print(f"Listening on topic: {TOPIC_CATEGORIZED}")

    try:
        consumer = create_consumer()
        producer = create_producer()
        print("Assignment Service Listening...")
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}")
        return

    try:
        for message in consumer:
            try:
                event = message.value
                process_event(event, producer)
            except Exception as e:
                print(f"Error processing message: {e}")
                continue

    except KeyboardInterrupt:
        print("\nStopping Assignment Service...")

    finally:
        consumer.close()
        producer.close()
        print("Kafka connections closed properly.")


if __name__ == "__main__":
    main()