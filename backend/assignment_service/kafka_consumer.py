import json
from kafka import KafkaConsumer

TOPIC = "complaints_topic"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    enable_auto_commit=True,
    group_id="assignment-group"
)

print("Assignment Service Listening...")

try:
    for message in consumer:
        event = message.value

        print("\nReceived Complaint Event:")
        print(event)

        # Assignment logic
        department = event["department"]

        print(f"Assigned to: {department}")

except KeyboardInterrupt:
    print("\nStopping Assignment Service...")

finally:
    consumer.close()
    print("Kafka Consumer closed properly.")