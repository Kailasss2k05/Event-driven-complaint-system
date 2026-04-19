#!/bin/bash

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."

while ! kafka-topics --bootstrap-server kafka:9092 --list > /dev/null 2>&1; do
  sleep 2
done

echo "Kafka is ready. Creating topics..."

# Create all complaint pipeline topics
TOPICS=(
  "complaint-submitted"
  "complaint-validated"
  "complaint-categorized"
  "complaint-assigned"
  "complaint-status-updated"
)

for TOPIC in "${TOPICS[@]}"; do
  echo "Creating topic: $TOPIC"
  kafka-topics --bootstrap-server kafka:9092 \
    --create \
    --if-not-exists \
    --topic "$TOPIC" \
    --partitions 3 \
    --replication-factor 1
done

echo ""
echo "All topics created successfully!"
echo ""

kafka-topics --bootstrap-server kafka:9092 --list
