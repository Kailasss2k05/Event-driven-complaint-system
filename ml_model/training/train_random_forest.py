# train_random_forest.py

import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# ==============================
# 1. Load dataset
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "dataset", "municipal_complaints.csv")
df = pd.read_csv(DATA_PATH)

# ==============================
# 2. Cleaning
# ==============================
df.columns = df.columns.str.strip()
df = df.dropna(subset=["Complaint_Description", "Department"])

df["Complaint_Description"] = (
    df["Complaint_Description"]
    .astype(str)
    .str.lower()
    .str.strip()
)

df["Department"] = df["Department"].astype(str).str.strip()
df = df.drop_duplicates()
# ==============================
# 3. Features / Labels
# ==============================
X = df["Complaint_Description"]
y_dept = df["Category"]

# ==============================
# 4. Train Test Split
# ==============================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    df["Category"],
    test_size=0.2,
    random_state=42,
    stratify=df["Category"]
)

# ==============================
# 5. TF-IDF (IMPROVED)
# ==============================
vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=5000,
    ngram_range=(1, 2),
    min_df=3,
    max_df=0.85,
    sublinear_tf=True
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# ==============================
# 6. Random Forest
# ==============================
rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=18,
    min_samples_split=8,
    min_samples_leaf=4,
    max_features="sqrt",
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

rf_model.fit(X_train_vec, y_train)
# ==============================
# 7. Evaluation
# ==============================

# ----- Department Model Evaluation -----
y_pred = rf_model.predict(X_test_vec)

print("\n==============================")
print("CATEGORY MODEL EVALUATION")
print("==============================")

print("\nTrain Accuracy :", rf_model.score(X_train_vec, y_train))
print("Test Accuracy  :", accuracy_score(y_test, y_pred))

print("\nClassification Report:\n")
print(classification_report(y_test, y_pred, zero_division=0))

# ==============================
# 8. Save
# ==============================
MODELS_DIR = os.path.join(BASE_DIR, "..", "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)

joblib.dump(rf_model, 
            os.path.join(MODELS_DIR, "category_model.pkl"))
joblib.dump(vectorizer, 
            os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl"))

print("\nRandom Forest model saved successfully!")
