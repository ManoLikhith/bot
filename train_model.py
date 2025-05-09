# Import necessary functions
from model.chatbot_model import load_dataset, train_model

# Load the dataset
dataset = load_dataset('data/food_ordering_dataset.json')

# Train the model
models, vectorizer = train_model(dataset)
