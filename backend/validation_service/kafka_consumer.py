import os
import json
import base64
import logging
from kafka import KafkaConsumer, KafkaProducer
from dotenv import load_dotenv
import sys

# Add project root to sys.path so `backend.*` imports in database.py resolve
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db.database import update_complaint_status, get_recent_complaints_by_user

# Load environment variables
load_dotenv()

# Kafka Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
TOPIC_SUBMITTED = os.getenv("TOPIC_COMPLAINT_SUBMITTED")
TOPIC_VALIDATED = os.getenv("TOPIC_COMPLAINT_VALIDATED")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load validation rules from external config file
def load_validation_rules():
    """Load profanity words and spam patterns from config file"""
    config_path = os.path.join(os.path.dirname(__file__), 'validation_rules.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
            
            # Check if profanity words are Base64 encoded
            if 'profanity_words_encoded' in rules:
                # Decode Base64 profanity words
                encoded_words = rules.get('profanity_words_encoded', [])
                profanity_words = set()
                for encoded in encoded_words:
                    try:
                        decoded = base64.b64decode(encoded).decode('utf-8')
                        profanity_words.add(decoded)
                    except Exception as e:
                        logger.warning(f"Failed to decode profanity word: {e}")
                return profanity_words, rules.get('spam_patterns', [])
            else:
                # Fallback to plain text profanity words
                return set(rules.get('profanity_words', [])), rules.get('spam_patterns', [])
    except FileNotFoundError:
        logger.warning(f"Validation rules file not found at {config_path}. Using empty rules.")
        return set(), []
    except Exception as e:
        logger.error(f"Failed to load validation rules: {e}")
        return set(), []

# Load rules at startup
PROFANITY_WORDS, SPAM_PATTERNS = load_validation_rules()
logger.info(f"Loaded {len(PROFANITY_WORDS)} profanity words and {len(SPAM_PATTERNS)} spam patterns")


def validate_length(description: str) -> tuple[bool, str]:
    """Validate complaint description length"""
    length = len(description.strip())
    
    if length < 10:
        return False, "Complaint description too short (minimum 10 characters)"
    
    if length > 5000:
        return False, "Complaint description too long (maximum 5000 characters)"
    
    return True, ""


def detect_profanity(description: str) -> tuple[bool, str]:
    """Check for profanity in complaint description"""
    description_lower = description.lower()
    
    for word in PROFANITY_WORDS:
        if word in description_lower:
            return False, "Complaint contains inappropriate language"
    
    return True, ""


def detect_spam(description: str) -> tuple[bool, str]:
    """Detect spam patterns in complaint description"""
    description_lower = description.lower()
    
    # Check for spam patterns
    for pattern in SPAM_PATTERNS:
        if pattern in description_lower:
            return False, "Complaint flagged as potential spam"
    
    # Check for excessive capitalization (>70% caps)
    if len(description) > 10:
        caps_count = sum(1 for c in description if c.isupper())
        caps_ratio = caps_count / len(description)
        if caps_ratio > 0.7:
            return False, "Complaint contains excessive capitalization"
    
    # Check for excessive punctuation (>10% of text)
    punct_count = sum(1 for c in description if c in '!?.')
    if len(description) > 10 and punct_count / len(description) > 0.1:
        return False, "Complaint contains excessive punctuation"
    
    return True, ""


def detect_duplicate(user_id: int, description: str, current_complaint_id: str = None) -> tuple[bool, str]:
    """Check for duplicate complaints from same user (within 12 hours)"""
    try:
        recent_complaints = get_recent_complaints_by_user(user_id, minutes=1440)  
        
        # Simple fuzzy matching - check if description is 90%+ similar
        description_lower = description.lower().strip()
        
        for complaint in recent_complaints:
            # Skip the current complaint itself to avoid self-duplicate detection
            if current_complaint_id and complaint.get('complaint_id') == current_complaint_id:
                continue
            existing_desc = complaint.get('description', '').lower().strip()
            
            # Calculate simple similarity (exact match)
            if description_lower == existing_desc:
                return False, f"Duplicate complaint detected (ID: {complaint['complaint_id']})"
            
            # Check for very similar complaints (>90% character overlap)
            if len(description_lower) > 10 and len(existing_desc) > 10:
                shorter = min(description_lower, existing_desc, key=len)
                longer = max(description_lower, existing_desc, key=len)
                if shorter in longer:
                    return False, f"Similar complaint already submitted (ID: {complaint['complaint_id']})"
        
        return True, ""
    
    except Exception as e:
        logger.error(f"Error checking for duplicates: {e}")
        # On error, allow the complaint through (don't block due to technical issue)
        return True, ""


def validate_complaint(event: dict) -> tuple[bool, str]:
    """Run all validation checks on a complaint"""
    complaint_id = event.get('complaint_id')
    description = event.get('description', '')
    user_id = event.get('user_id')
    
    logger.info(f"Validating complaint {complaint_id}...")
    
    # Length validation
    valid, reason = validate_length(description)
    if not valid:
        logger.warning(f"Complaint {complaint_id} failed length check: {reason}")
        return False, reason
    
    # Profanity check
    valid, reason = detect_profanity(description)
    if not valid:
        logger.warning(f"Complaint {complaint_id} failed profanity check: {reason}")
        return False, reason
    
    # Spam detection
    valid, reason = detect_spam(description)
    if not valid:
        logger.warning(f"Complaint {complaint_id} failed spam check: {reason}")
        return False, reason
    
    # Duplicate detection
    valid, reason = detect_duplicate(user_id, description, current_complaint_id=complaint_id)
    if not valid:
        logger.warning(f"Complaint {complaint_id} failed duplicate check: {reason}")
        return False, reason
    
    logger.info(f"Complaint {complaint_id} passed all validations ✓")
    return True, ""


def process_event(event, producer):
    """Process submitted complaint and validate it"""
    try:
        complaint_id = event.get('complaint_id')
        
        # Run validation checks
        is_valid, rejection_reason = validate_complaint(event)
        
        if is_valid:
            # Complaint is valid - publish to validated topic
            validated_event = event.copy()
            validated_event['validation_status'] = 'PASSED'
            
            producer.send(TOPIC_VALIDATED, validated_event)
            logger.info(f"✓ Complaint {complaint_id} validated and forwarded to {TOPIC_VALIDATED}")
        
        else:
            # Complaint is rejected - update status in DB
            update_complaint_status(complaint_id, 'REJECTED', rejection_reason)
            
            logger.warning(f"✗ Complaint {complaint_id} REJECTED: {rejection_reason}")
            
            # Optionally publish rejection event (for notification service)
            rejection_event = {
                'complaint_id': complaint_id,
                'user_id': event.get('user_id'),
                'status': 'REJECTED',
                'reason': rejection_reason,
                'timestamp': event.get('timestamp')
            }
            # You can publish to a rejection topic if needed
            # producer.send('complaint-rejected', rejection_event)
    
    except Exception as e:
        logger.error(f"Error processing event: {e}")


def main():
    """Start Kafka consumer for validation service"""
    logger.info(f"Validation Service connecting to Kafka at {KAFKA_BROKER}...")
    logger.info(f"Listening on topic: {TOPIC_SUBMITTED}")
    
    try:
        # Initialize Kafka Consumer
        consumer = KafkaConsumer(
            TOPIC_SUBMITTED,
            bootstrap_servers=[KAFKA_BROKER],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='validation-service-group'
        )
        
        # Initialize Kafka Producer
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        logger.info("Validation Service started successfully! Waiting for complaints...")
        
        # Process messages
        for message in consumer:
            event = message.value
            logger.info(f"Received complaint: {event.get('complaint_id')}")
            process_event(event, producer)
    
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        return


if __name__ == "__main__":
    main()
