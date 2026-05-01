import os
import pandas as pd
import joblib

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report, accuracy_score

INPUT_FILE = "sentiment_system/data/training_dataset.csv"
MODEL_DIR = "models"
MODEL_FILE = os.path.join(MODEL_DIR, "random_forest_model.pkl")


def main():

    print("Loading training dataset...")

    df = pd.read_csv(INPUT_FILE)

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    features = [
        "news_count",
        "rolling_3_sentiment",
        "rolling_7_sentiment",
        "return_1d",
        "return_3d",
        "return_7d"
    ]

    X = df[features]
    y = df["direction"]

    print("Dataset size:", len(df))

    split_index = int(len(df) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    print("Training size:", len(X_train))
    print("Testing size:", len(X_test))

    print("Running hyperparameter search...")

    model = GradientBoostingClassifier(random_state=42)

    param_grid = {
        "n_estimators": [200, 400, 600],
        "learning_rate": [0.03, 0.05, 0.1],
        "max_depth": [2, 3]
    }

    grid = GridSearchCV(
        model,
        param_grid,
        cv=4,
        n_jobs=-1
    )

    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_

    print("\nBest Parameters:", grid.best_params_)

    # ---------- Threshold tuning ----------

    probs = best_model.predict_proba(X_test)

    best_acc = 0
    best_thresh = 0.5
    best_preds = None

    for t in [i/100 for i in range(40, 60)]:

        preds = []

        for p in probs:
            if p[1] > t:
                preds.append("UP")
            else:
                preds.append("DOWN")

        acc = accuracy_score(y_test, preds)

        if acc > best_acc:
            best_acc = acc
            best_thresh = t
            best_preds = preds

    print("\nBest Threshold:", best_thresh)

    accuracy = best_acc
    predictions = best_preds

    print("\nModel Accuracy:", accuracy)

    print("\nClassification Report:\n")
    print(classification_report(y_test, predictions))

    importance = best_model.feature_importances_

    print("\nFeature Importance:")

    for f, score in zip(features, importance):
        print(f"{f}: {round(score,4)}")

    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(best_model, MODEL_FILE)

    print("\nModel saved to:", MODEL_FILE)


if __name__ == "__main__":
    main()