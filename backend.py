# backend.py
from flask import Flask, request, jsonify
from model.chatbot_model import load_dataset, train_model, get_response, load_menu
from database import init_db, save_order, track_order
import re
import random
import time

app = Flask(__name__)

# Load chatbot model and data
dataset = load_dataset('data/food_ordering_dataset.json')
models, vectorizer = train_model(dataset)
menu = load_menu()
init_db()

# Exchange rate: 1 USD = 83 INR
EXCHANGE_RATE = 83

class OrderManager:
    def __init__(self):
        self.current_order = {}
        self.order_confirmed = False
        self.order_id = None
        self.stage = "init"

    def reset_order(self):
        self.current_order = {}
        self.order_confirmed = False
        self.order_id = None
        self.stage = "init"

    def generate_order_id(self):
        self.order_id = f"ORD-{int(time.time())}-{random.randint(1000, 9999)}"
        return self.order_id

    def extract_quantity_and_item(self, text):
        quantity_pattern = r'\b(\d+)\b|\b(one|two|three|four|five|six|seven|eight|nine|ten)\b'
        matches = re.findall(quantity_pattern, text.lower())
        quantity = 1
        item = text
        
        if matches:
            quantity_str = next((x for t in matches for x in t if x), '1')
            word_to_num = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4,
                'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
                'nine': 9, 'ten': 10
            }
            quantity = word_to_num.get(quantity_str.lower(), quantity_str)
            try:
                quantity = int(quantity)
            except ValueError:
                quantity = 1
            item = re.sub(quantity_pattern, '', text, count=1).strip()
            item = re.sub(r'\s+', ' ', item).strip()
        
        return quantity, item

    def add_to_order(self, item_text):
        if not menu or 'menu' not in menu:
            return False, "Menu not available. Please try again later."
        
        quantity, item_name = self.extract_quantity_and_item(item_text)
        menu_item = next((item for item in menu['menu'] 
                         if item['name'].lower() in item_name.lower()), None)
        
        if menu_item:
            price_inr = menu_item['price'] * EXCHANGE_RATE
            if menu_item['name'] in self.current_order:
                self.current_order[menu_item['name']]['quantity'] += quantity
            else:
                self.current_order[menu_item['name']] = {
                    'quantity': quantity,
                    'price': price_inr,
                    'category': menu_item['category']
                }
            return True, f"Added {quantity}x {menu_item['name']}"
        return False, "Item not found. Please check the menu and try again."

    def remove_from_order(self, item_name):
        item = next((name for name in self.current_order 
                    if item_name.lower() in name.lower()), None)
        if item:
            del self.current_order[item]
            return True, f"Removed {item}"
        return False, "Item not in order."

    def get_order_summary(self):
        if not self.current_order:
            return "No items in your current order."
        summary = "Current Order:\n"
        total = 0
        for item, details in self.current_order.items():
            summary += f"- {details['quantity']}x {item} (₹{details['price']:.2f} each)\n"
            total += details['quantity'] * details['price']
        summary += f"\nTotal: ₹{total:.2f}"
        return summary

    def save_order_to_db(self):
        if not self.current_order:
            return False
        order_items = "; ".join([f"{details['quantity']}x {item} (₹{details['price']:.2f})" 
                                 for item, details in self.current_order.items()])
        return save_order(self.order_id, order_items)

# Global order manager instance (for simplicity; in production, use session or database)
order_manager = OrderManager()

@app.route('/')
def serve_homepage():
    return app.send_static_file('index.html')

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    user_text = data.get('message', '').strip()
    if not user_text:
        return jsonify({'response': 'Please type a message.'})

    if user_text.lower() == "exit":
        order_manager.reset_order()
        return jsonify({'response': 'Goodbye! Thanks for visiting!'})

    if "track" in user_text.lower():
        order_id_match = re.search(r'track\s+([A-Z0-9-]+)', user_text, re.IGNORECASE)
        if order_id_match:
            order_id = order_id_match.group(1)
            result = track_order(order_id)
            if result:
                items, status, timestamp = result
                response = f"Order ID: {order_id}\nItems: {items}\nStatus: {status}\nPlaced on: {timestamp}"
            else:
                response = f"No order found with ID: {order_id}. Please check the ID and try again."
        else:
            response = "Please provide an order ID like this: 'track ORD-1234567890-1234'"
        return jsonify({'response': response})

    if order_manager.order_confirmed:
        if "new order" in user_text.lower():
            order_manager.reset_order()
            response = "Starting a new order! Would you like to place an order? (yes/no)"
        else:
            response = get_response(user_text, models, vectorizer, dataset)
        return jsonify({'response': response})

    # Process order flow
    intent_response = get_response(user_text, models, vectorizer, dataset)
    intent = predict_intent(user_text)

    if order_manager.stage == "init":
        if intent == "order" or is_positive_response(user_text):
            order_manager.stage = "collecting"
            menu_response = format_menu()
            response = f"Great! Here's our menu:\n{menu_response}\nWhat would you like to order?"
        elif intent in ["greeting", "menu", "feedback", "track"]:
            response = intent_response
        else:
            response = "Would you like to place an order? (yes/no)"
    
    elif order_manager.stage == "collecting":
        if is_negative_response(user_text):
            order_manager.stage = "confirmation"
            summary = order_manager.get_order_summary()
            response = f"{summary}\n\nWould you like to confirm this order? (yes/no)"
        else:
            success, message = order_manager.add_to_order(user_text)
            if success:
                response = f"{message}\n{order_manager.get_order_summary()}\nWould you like to add anything else? (yes/no)"
            else:
                response = f"{message}\nPlease choose from the menu:\n{format_menu()}"

    elif order_manager.stage == "confirmation":
        if is_positive_response(user_text):
            order_id = order_manager.generate_order_id()
            order_manager.order_confirmed = True
            order_manager.save_order_to_db()
            response = f"Order confirmed! 🎉 Your Order ID: {order_id}\nThank you for your order! Type 'track <order_id>' to check status or 'new order' to start again."
        elif is_negative_response(user_text):
            order_manager.stage = "modifying"
            response = "Let's modify your order. Add or remove items (e.g., 'remove pizza' or 'add burger')."
        else:
            response = "Please respond with 'yes' or 'no' to confirm your order."

    elif order_manager.stage == "modifying":
        if "remove" in user_text.lower():
            item = user_text.lower().replace("remove", "").strip()
            success, message = order_manager.remove_from_order(item)
            response = message
        else:
            success, message = order_manager.add_to_order(user_text)
            response = message
        response += f"\n{order_manager.get_order_summary()}\nWould you like to confirm this order? (yes/no)"
        order_manager.stage = "confirmation"

    return jsonify({'response': response})

def predict_intent(user_text):
    user_input_vectorized = vectorizer.transform([user_text.lower()])
    probabilities = {name: model.predict_proba(user_input_vectorized)[0].max() 
                     for name, model in models.items()}
    best_model = max(probabilities, key=probabilities.get)
    return models[best_model].predict(user_input_vectorized)[0]

def format_menu():
    if not menu or 'menu' not in menu:
        return "Menu unavailable."
    response = ""
    categories = {item['category'] for item in menu['menu']}
    for category in categories:
        response += f"\n{category}:\n"
        for item in menu['menu']:
            if item['category'] == category:
                price_inr = item['price'] * EXCHANGE_RATE
                response += f"- {item['name']} (₹{price_inr:.2f})\n"
    return response

def is_positive_response(text):
    return any(word in text.lower() for word in ["yes", "yeah", "yep", "sure", "confirm"])

def is_negative_response(text):
    return any(word in text.lower() for word in ["no", "nope", "nah", "not", "cancel"])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)