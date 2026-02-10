import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "saved_models")

# Load category model and vectorizer
category_model = joblib.load(
    os.path.join(MODELS_DIR, "category_model.pkl")
)

vectorizer = joblib.load(
    os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")
)

while True:
    user_input = input("\nEnter complaint (type exit to stop): ")

    if user_input.lower() == "exit":
        break

    # Transform input
    X_vec = vectorizer.transform([user_input])

    # Predict category
    category_pred = category_model.predict(X_vec)[0]

    print("\nPrediction Result")
    print("Category :", category_pred)