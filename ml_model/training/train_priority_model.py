import os
import pandas as pd
import joblib

from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# 1. Load Dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "..",
    "dataset",
    "municipal_complaints.csv"
)

df = pd.read_csv(DATA_PATH)

# 2. Cleaning
df.columns = df.columns.str.strip()

df = df.dropna(
    subset=["Complaint_Description", "Priority", "Severity"]
)

df["Complaint_Description"] = (
    df["Complaint_Description"]
    .astype(str)
    .str.lower()
    .str.strip()
)

df["model_text"] = (
    df["Complaint_Description"] + " " + df["Severity"]
)

texts = df["model_text"]
labels = df["Priority"]

# 3. Distribution Check
print("\nPriority Distribution:\n")
print(labels.value_counts())

# 4. Train Test Split
X_train, X_test, y_train, y_test = train_test_split(
    texts,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels
)

# 5. Sentence Transformer
print("\nLoading Sentence Transformer...")

transformer = SentenceTransformer("all-mpnet-base-v2")

print("\nEncoding training data...")
X_train_emb = transformer.encode(
    X_train.tolist(),
    show_progress_bar=True
)

print("\nEncoding testing data...")
X_test_emb = transformer.encode(
    X_test.tolist(),
    show_progress_bar=True
)

# 6. Random Forest Model
priority_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=20,
    class_weight="balanced",
    random_state=42
)

priority_model.fit(X_train_emb, y_train)

# 7. Evaluation
y_pred = priority_model.predict(X_test_emb)

print("\n==============================")
print("PRIORITY MODEL EVALUATION")
print("==============================")

print("\nTrain Accuracy :",
      priority_model.score(X_train_emb, y_train))

print("Test Accuracy  :",
      accuracy_score(y_test, y_pred))

print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

# 8. Save Model
SAVE_DIR = os.path.join(
    BASE_DIR,
    "..",
    "saved_models",
    "Priority"
)

os.makedirs(SAVE_DIR, exist_ok=True)

joblib.dump(
    priority_model,
    os.path.join(SAVE_DIR, "priority_model.pkl")
)

print("\nPriority model saved successfully!")