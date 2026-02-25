import os
import pandas as pd
import joblib
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

# 0. Project Paths

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "municipal_complaints.csv"
)

MODEL_DIR = os.path.join(BASE_DIR, "saved_models","Category")


# 1. Load Dataset

df = pd.read_csv(DATASET_PATH)

df.columns = df.columns.str.strip().str.lower()

df["complaint_description"] = (
    df["complaint_description"]
    .astype(str)
    .str.strip()
)

df["category"] = (
    df["category"]
    .astype(str)
    .str.strip()
)

X = df["complaint_description"]
y = df["category"]


# 2. Train Test Split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# 3. Load Transformer Model

print("\nLoading transformer model...")
embedder = SentenceTransformer("all-mpnet-base-v2")

print("Generating embeddings...")
X_train_emb = embedder.encode(
    X_train.tolist(),
    show_progress_bar=True
)

X_test_emb = embedder.encode(
    X_test.tolist(),
    show_progress_bar=True
)


# 4. Train Classifier

print("\nTraining classifier...")
model = LogisticRegression(max_iter=1000)
model.fit(X_train_emb, y_train)

# 5. Evaluation

y_pred = model.predict(X_test_emb)

print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

# 6. Save Model

os.makedirs(MODEL_DIR, exist_ok=True)

model_package = {
    "model": model,
    "embedder": "all-mpnet-base-v2"
}

joblib.dump(
    model_package,
    os.path.join(MODEL_DIR, "category_model.pkl")
)

# Save embedding name to text file
with open(os.path.join(MODEL_DIR, "embedding.txt"), "w") as f:
    f.write("all-mpnet-base-v2")

print("\nCategory model and embedding info saved!")

# 7. Main Execution

if __name__ == "__main__":
    print("\nTraining completed successfully!")