import os
import json
from dotenv import load_dotenv
from kafka import KafkaConsumer

load_dotenv()

# Add project root to path for DB imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.db.database import insert_event

KAFKA_BROKER = os.getenv("KAFKA_BROKER")

# Listen to all pipeline topics
TOPICS = [
    os.getenv("TOPIC_COMPLAINT_SUBMITTED"),
    os.getenv("TOPIC_COMPLAINT_VALIDATED"),
    os.getenv("TOPIC_COMPLAINT_CATEGORIZED"),
    os.getenv("TOPIC_COMPLAINT_ASSIGNED"),
    os.getenv("TOPIC_COMPLAINT_STATUS_UPDATED"),
]

# Remove None values (topics not set in .env)
TOPICS = [t for t in TOPICS if t]


def create_consumer():
    return KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="audit-group"
    )


def process_event(topic, event):
    """Log every event to the audit trail."""
    complaint_id = event.get("complaint_id", "unknown")
    status = event.get("status", "UNKNOWN")

    print(f"\n[AUDIT] Topic: {topic}")
    print(f"  Complaint: {complaint_id}")
    print(f"  Status: {status}")
    print(f"  Data: {json.dumps(event, indent=2)}")

    try:
        insert_event(complaint_id, topic, event, status)
        print(f"  -> Logged to database")
    except Exception as e:
        print(f"  -> Failed to log: {e}")


def main():
    print(f"Audit Service connecting to Kafka at {KAFKA_BROKER}...")
    print(f"Listening on topics: {TOPICS}")

    try:
        consumer = create_consumer()
        print("Audit Service Listening...")
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}")
        return

    try:
        for message in consumer:
            try:
                topic = message.topic
                event = message.value
                process_event(topic, event)
            except Exception as e:
                print(f"Error processing message: {e}")
                continue

    except KeyboardInterrupt:
        print("\nStopping Audit Service...")

    finally:
        consumer.close()
        print("Audit Service closed properly.")


if __name__ == "__main__":
    main()
