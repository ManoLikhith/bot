# chatbot_model.py (updated)
import json
import random
import logging
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV

# Keep all the previous functions (load_dataset, load_menu, train_model, get_response)
# from the previous implementation exactly as they were
# Only remove any Flask-specific code if present

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename='training.log', level=logging.INFO)

def load_dataset(file_path):
    """Load the dataset from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        logger.info("Dataset loaded successfully.")
        return data
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise

def load_menu(file_path='data/menu.json'):
    """Load the menu from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            menu_data = json.load(file)
        logger.info("Menu loaded successfully.")
        return menu_data
    except Exception as e:
        logger.error(f"Error loading menu: {e}")
        return None

def train_model(dataset):
    """Train the models using the dataset."""
    logger.info("Starting model training...")
    
    try:
        # Prepare data
        intents = dataset['intents']
        X = []
        y = []
        for intent in intents:
            for pattern in intent['patterns']:
                X.append(pattern.lower())
                y.append(intent['tag'])

        if not X or not y:
            raise ValueError("No training data found in dataset.")

        # Split dataset
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Vectorize text data
        vectorizer = TfidfVectorizer()
        X_train_counts = vectorizer.fit_transform(X_train)
        X_test_counts = vectorizer.transform(X_test)

        # Initialize models
        models = {
            'naive_bayes': MultinomialNB(),
            'svm': SVC(probability=True),
            'random_forest': RandomForestClassifier(n_estimators=100)
        }

        # Hyperparameter tuning for SVM
        param_grid = {'C': [0.1, 1, 10], 'kernel': ['linear', 'rbf']}
        svm_grid = GridSearchCV(SVC(probability=True), param_grid, cv=5)
        svm_grid.fit(X_train_counts, y_train)
        models['svm'] = svm_grid.best_estimator_
        logger.info(f"SVM best parameters: {svm_grid.best_params_}")

        # Train other models
        for model_name, model in models.items():
            if model_name != 'svm':
                model.fit(X_train_counts, y_train)
            logger.info(f"{model_name} training completed.")
            
            # Evaluate model
            accuracy = model.score(X_test_counts, y_test)
            logger.info(f"{model_name} accuracy: {accuracy:.2f}")

        # Save models and vectorizer
        for model_name, model in models.items():
            joblib.dump(model, f"model/{model_name}_model.pkl")
        joblib.dump(vectorizer, 'model/vectorizer.pkl')
        logger.info("Models and vectorizer saved successfully.")
        
        return models, vectorizer

    except Exception as e:
        logger.error(f"Error during model training: {e}")
        raise

def get_response(user_input, models, vectorizer, dataset):
    """Generate a response based on user input and trained models."""
    try:
        # Vectorize user input
        user_input_vectorized = vectorizer.transform([user_input.lower()])
        
        # Get predictions and probabilities
        predictions = {}
        probabilities = {}
        for name, model in models.items():
            predictions[name] = model.predict(user_input_vectorized)[0]
            probabilities[name] = model.predict_proba(user_input_vectorized)[0].max()
        
        # Select best prediction
        best_model = max(probabilities, key=probabilities.get)
        predicted_intent = predictions[best_model]
        
        # Handle menu intent
        if predicted_intent == 'menu':
            menu_data = load_menu()
            if menu_data:
                response = "Here's our menu:<br>"
                categories = {item['category'] for item in menu_data['menu']}
                for category in categories:
                    response += f"<br><b>{category}</b>:<br>"
                    for item in menu_data['menu']:
                        if item['category'] == category:
                            response += f"- {item['name']} (${item['price']}): {item['description']}<br>"
            else:
                response = "Our menu is currently unavailable. Please check back later."
        else:
            # Find response from dataset
            response = "I'm sorry, I didn't understand that. How can I assist you?"
            for intent in dataset['intents']:
                if intent['tag'] == predicted_intent:
                    response = random.choice(intent['responses'])
                    break

        return response
    
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "Something went wrong. Please try again."

if __name__ == "__main__":
    dataset = load_dataset('data/food_ordering_dataset.json')
    models, vectorizer = train_model(dataset)