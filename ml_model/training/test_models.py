import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "saved_models")

dept_model = joblib.load(os.path.join(MODELS_DIR, "random_forest_model.pkl"))
priority_model = joblib.load(os.path.join(MODELS_DIR, "priority_model.pkl"))
vectorizer = joblib.load(os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl"))

while True:
    user_input = input("\nEnter complaint (type exit to stop): ")

    if user_input.lower() == "exit":
        break

    X_vec = vectorizer.transform([user_input])

    dept_pred = dept_model.predict(X_vec)[0]
    pri_pred = priority_model.predict(X_vec)[0]

    print("\nPrediction Result")
    print("Department :", dept_pred)
    print("Priority   :", pri_pred)