import re
import tkinter as tk
from tkinter import scrolledtext, messagebox, font as tkfont
from model.chatbot_model import load_dataset, train_model, get_response, load_menu
import logging
import random
import time
from database import init_db, save_order, track_order
from itertools import cycle

# Exchange rate: 1 USD = 83 INR (adjust as needed)
EXCHANGE_RATE = 83

class OrderManager:
    def __init__(self):
        self.current_order = {}
        self.order_confirmed = False
        self.order_id = None
        self.menu = load_menu()
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
        if not self.menu or 'menu' not in self.menu:
            return False, "Menu not available. Please try again later."
        
        quantity, item_name = self.extract_quantity_and_item(item_text)
        menu_item = next((item for item in self.menu['menu'] 
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

class ChatApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Food Order Chatbot")
        self.root.geometry("900x700")
        self.root.configure(bg="#121212")
        
        # Enhanced fonts
        self.title_font = ("Verdana", 14, "bold")
        self.chatbot_font = ("Segoe UI", 12, "italic")
        self.user_font = ("Segoe UI", 12, "bold")
        self.menu_category_font = ("Georgia", 12, "bold")
        self.menu_item_font = ("Calibri", 11)
        self.menu_price_font = ("Consolas", 11, "bold")
        self.button_font = ("Segoe UI", 11, "bold")
        
        # Vibrant color scheme for menu
        self.menu_colors = {
            'category': "#FF6B6B",  # Coral red
            'item': "#F8F8F8",     # Off-white
            'price': "#4ECDC4",     # Mint green
            'separator': "#424242"   # Dark gray
        }
        
        self.center_window()
        self.gradient_colors = cycle(["#1a1a2e", "#16213e", "#0f3460", "#1f1f3d"])
        self.current_bg = next(self.gradient_colors)
        
        self.order_manager = OrderManager()
        self.initialize_chatbot()
        self.create_widgets()
        self.animate_background()

    def center_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 900
        window_height = 700
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    def animate_background(self):
        self.current_bg = next(self.gradient_colors)
        self.root.configure(bg=self.current_bg)
        self.main_frame.configure(bg=self.current_bg)
        self.root.after(3000, self.animate_background)

    def initialize_chatbot(self):
        try:
            self.dataset = load_dataset('data/food_ordering_dataset.json')
            self.models, self.vectorizer = train_model(self.dataset)
            logging.info("Chatbot initialized successfully")
        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            messagebox.showerror("Error", "Failed to initialize chatbot. Please restart.")
            self.root.quit()

    def create_widgets(self):
        self.main_frame = tk.Frame(
            self.root, 
            bg=self.current_bg,
            bd=0,
            highlightthickness=2,
            highlightbackground="#444"
        )
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.header_frame = tk.Frame(
            self.main_frame, 
            bg=self.current_bg,
            pady=10
        )
        self.header_frame.pack(fill="x")
        
        self.title_label = tk.Label(
            self.header_frame,
            text="🍔 Food Ordering Bot 🍕",
            font=self.title_font,
            fg="#FFD166",
            bg=self.current_bg
        )
        self.title_label.pack()
        
        self.chat_frame = tk.Frame(
            self.main_frame,
            bg="#1e1e2f",
            bd=2,
            relief="groove",
            highlightthickness=0
        )
        self.chat_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        
        self.chat_history = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            width=85,
            height=25,
            state='disabled',
            bg="#1e1e2f",
            fg="#e0e0e0",
            font=("Segoe UI", 11),
            insertbackground="#ffeb3b",
            relief="flat",
            padx=10,
            pady=10,
            borderwidth=0
        )
        self.chat_history.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.input_frame = tk.Frame(
            self.main_frame,
            bg=self.current_bg,
            pady=5
        )
        self.input_frame.pack(fill="x", padx=5)
        
        self.user_input = tk.Entry(
            self.input_frame,
            width=70,
            bg="#2d2d3d",
            fg="#ffffff",
            font=self.user_font,
            insertbackground="#00e6cc",
            relief="flat",
            borderwidth=2,
            highlightthickness=1,
            highlightcolor="#ff5722",
            highlightbackground="#444"
        )
        self.user_input.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )
        self.user_input.bind("<Return>", self.send_message)
        self.user_input.bind("<FocusIn>", self.on_entry_focus_in)
        self.user_input.bind("<FocusOut>", self.on_entry_focus_out)
        
        self.send_btn = tk.Button(
            self.input_frame,
            text="SEND",
            command=self.send_message,
            width=10,
            bg="#06D6A0",
            fg="#ffffff",
            font=self.button_font,
            activebackground="#48BFE3",
            activeforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            cursor="hand2"
        )
        self.send_btn.pack(side="right")
        
        self.send_btn.bind("<Enter>", lambda e: self.send_btn.config(bg="#48BFE3"))
        self.send_btn.bind("<Leave>", lambda e: self.send_btn.config(bg="#06D6A0"))
        
        self.update_chat("Chatbot", "Welcome to FoodBot! 😊 Would you like to place an order? (yes/no)")

    def on_entry_focus_in(self, event):
        self.user_input.config(highlightcolor="#FF6B6B")

    def on_entry_focus_out(self, event):
        self.user_input.config(highlightcolor="#444")

    def update_chat(self, sender, message):
        self.chat_history.configure(state='normal')
        
        self.chat_history.tag_config(
            "chatbot",
            foreground="#4FC3F7",
            font=self.chatbot_font,
            lmargin1=20,
            lmargin2=20,
            rmargin=20
        )
        self.chat_history.tag_config(
            "user",
            foreground="#69F0AE",
            font=self.user_font,
            lmargin1=20,
            lmargin2=20,
            rmargin=20
        )
        self.chat_history.tag_config(
            "system",
            foreground="#FFAB40",
            font=("Segoe UI", 11, "bold"),
            justify="center"
        )
        
        if sender == "Chatbot":
            self.chat_history.insert(tk.END, f"{sender}: ", "chatbot")
            self.chat_history.insert(tk.END, f"{message}\n\n", "chatbot")
        elif sender == "You":
            self.chat_history.insert(tk.END, f"{sender}: ", "user")
            self.chat_history.insert(tk.END, f"{message}\n\n", "user")
        else:
            self.chat_history.insert(tk.END, f"{message}\n\n", "system")
        
        self.chat_history.configure(state='disabled')
        self.chat_history.yview(tk.END)

    def format_menu(self):
        """Format the menu with attractive styling and colors."""
        if not self.order_manager.menu or 'menu' not in self.order_manager.menu:
            return "Menu unavailable."
        
        # Configure tags for menu elements
        self.chat_history.tag_config(
            "menu_category",
            foreground=self.menu_colors['category'],
            font=self.menu_category_font,
            spacing3=5
        )
        self.chat_history.tag_config(
            "menu_item",
            foreground=self.menu_colors['item'],
            font=self.menu_item_font
        )
        self.chat_history.tag_config(
            "menu_price",
            foreground=self.menu_colors['price'],
            font=self.menu_price_font
        )
        self.chat_history.tag_config(
            "menu_separator",
            foreground=self.menu_colors['separator'],
            font=("Segoe UI", 4)
        )
        
        categories = {item['category'] for item in self.order_manager.menu['menu']}
        menu_text = ""
        
        for category in sorted(categories):
            # Add category header
            menu_text += f"{category.upper()}:\n"
            
            # Add items under this category
            for item in sorted(self.order_manager.menu['menu'], key=lambda x: x['name']):
                if item['category'] == category:
                    price_inr = item['price'] * EXCHANGE_RATE
                    name_length = len(item['name'])
                    padding = max(0, 25 - name_length)
                    menu_text += f"  • {item['name']}{' ' * padding}₹{price_inr:.2f}\n"
            
            # Add separator between categories
            menu_text += "\n"
        
        return menu_text

    def send_message(self, event=None):
        user_text = self.user_input.get().strip()
        if not user_text:
            return

        self.update_chat("You", user_text)
        self.user_input.delete(0, tk.END)

        try:
            if user_text.lower() == "exit":
                self.update_chat("Chatbot", "Goodbye! Thanks for visiting! 👋")
                self.root.after(1000, self.root.quit)
            elif "track" in user_text.lower():
                self.handle_order_tracking(user_text)
            elif self.order_manager.order_confirmed:
                self.handle_post_order(user_text)
            else:
                self.process_order_flow(user_text)
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            self.update_chat("Chatbot", "⚠️ Sorry, an error occurred. Please try again.")

    def process_order_flow(self, user_text):
        intent_response = get_response(user_text, self.models, self.vectorizer, self.dataset)
        intent = self.predict_intent(user_text)

        if self.order_manager.stage == "init":
            if intent == "order" or self.is_positive_response(user_text):
                self.order_manager.stage = "collecting"
                menu_response = self.format_menu()
                self.update_chat("Chatbot", f"Great! Here's our menu:\n{menu_response}\nWhat would you like to order?")
            elif intent in ["greeting", "menu", "feedback", "track"]:
                self.update_chat("Chatbot", intent_response)
            else:
                self.update_chat("Chatbot", "Would you like to place an order? (yes/no)")

        elif self.order_manager.stage == "collecting":
            if self.is_negative_response(user_text):
                self.order_manager.stage = "confirmation"
                summary = self.order_manager.get_order_summary()
                self.update_chat("Chatbot", f"{summary}\n\nWould you like to confirm this order? (yes/no)")
            else:
                success, message = self.order_manager.add_to_order(user_text)
                if success:
                    self.update_chat("Chatbot", "✅ " + message)
                    self.update_chat("Chatbot", self.order_manager.get_order_summary())
                    self.update_chat("Chatbot", "Would you like to add anything else? (yes/no)")
                else:
                    self.update_chat("Chatbot", f"❌ {message}\nPlease choose from the menu:\n{self.format_menu()}")

        elif self.order_manager.stage == "confirmation":
            if self.is_positive_response(user_text):
                order_id = self.order_manager.generate_order_id()
                self.order_manager.order_confirmed = True
                self.order_manager.save_order_to_db()
                self.update_chat("Chatbot", f"🎉 Order confirmed! Your Order ID: {order_id}")
                self.update_chat("Chatbot", "Thank you for your order! Type 'track <order_id>' to check status or 'new order' to start again.")
            elif self.is_negative_response(user_text):
                self.order_manager.stage = "modifying"
                self.update_chat("Chatbot", "Let's modify your order. Add or remove items (e.g., 'remove pizza' or 'add burger').")
            else:
                self.update_chat("Chatbot", "Please respond with 'yes' or 'no' to confirm your order.")

        elif self.order_manager.stage == "modifying":
            if "remove" in user_text.lower():
                item = user_text.lower().replace("remove", "").strip()
                success, message = self.order_manager.remove_from_order(item)
                self.update_chat("Chatbot", "❌ " + message)
            else:
                success, message = self.order_manager.add_to_order(user_text)
                self.update_chat("Chatbot", "✅ " + message)
            
            summary = self.order_manager.get_order_summary()
            self.update_chat("Chatbot", f"{summary}\nWould you like to confirm this order? (yes/no)")
            self.order_manager.stage = "confirmation"

    def handle_post_order(self, user_text):
        if "new order" in user_text.lower():
            self.order_manager.reset_order()
            self.update_chat("Chatbot", "🔄 Starting a new order! Would you like to place an order? (yes/no)")
        else:
            response = get_response(user_text, self.models, self.vectorizer, self.dataset)
            self.update_chat("Chatbot", response)

    def handle_order_tracking(self, user_text):
        order_id_match = re.search(r'track\s+([A-Z0-9-]+)', user_text, re.IGNORECASE)
        if order_id_match:
            order_id = order_id_match.group(1)
            result = track_order(order_id)
            if result:
                items, status, timestamp = result
                status_icon = "🟢" if status.lower() == "delivered" else "🟡" if status.lower() == "preparing" else "🔴"
                self.update_chat("Chatbot", f"📦 Order Tracking:\n\nOrder ID: {order_id}\nItems: {items}\nStatus: {status_icon} {status}\nPlaced on: {timestamp}")
            else:
                self.update_chat("Chatbot", f"❌ No order found with ID: {order_id}. Please check the ID and try again.")
        else:
            self.update_chat("Chatbot", "Please provide an order ID like this: 'track ORD-1234567890-1234'")

    def predict_intent(self, user_text):
        user_input_vectorized = self.vectorizer.transform([user_text.lower()])
        probabilities = {name: model.predict_proba(user_input_vectorized)[0].max() 
                         for name, model in self.models.items()}
        best_model = max(probabilities, key=probabilities.get)
        return self.models[best_model].predict(user_input_vectorized)[0]

    def is_positive_response(self, text):
        return any(word in text.lower() for word in ["yes", "yeah", "yep", "sure", "confirm", "ok", "okay"])

    def is_negative_response(self, text):
        return any(word in text.lower() for word in ["no", "nope", "nah", "not", "cancel", "stop"])

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='chatbot.log'
    )
    
    init_db()
    root = tk.Tk()
    app = ChatApplication(root)
    root.mainloop()