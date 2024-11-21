import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

raw_data = pd.read_csv("Healthcare-stroke-data.csv") # The dataset in my zipfile
data = pd.DataFrame(raw_data)

X = data.drop(columns=['STROKE'], axis=1)  # 'STROKE' is the target variable we want to predict
y = data['STROKE']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = joblib.load("stroke_model.pkl")
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred))