# main.py (updated)
from model.chatbot_model import load_dataset, get_response, train_model  # Ensure train_model is imported

if __name__ == "__main__":
    dataset = load_dataset('data/food_ordering_dataset.json')
    models, vectorizer = train_model(dataset)
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Chatbot: Goodbye!")
            break
        response = get_response(user_input, models, vectorizer, dataset)  # Add dataset
        print("Chatbot:", response)
