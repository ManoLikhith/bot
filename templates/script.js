// script.js
const menuItems = [
    {
        id: 1,
        name: "Margherita Pizza",
        description: "Classic pizza with fresh mozzarella, tomatoes, and basil.",
        price: 12.99,
        category: "Pizza",
        image: "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60"
    },
    {
        id: 2,
        name: "Pepperoni Pizza",
        description: "Delicious pizza topped with pepperoni and mozzarella cheese.",
        price: 14.99,
        category: "Pizza",
        image: "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60"
    },
    {
        id: 3,
        name: "Caesar Salad",
        description: "Crisp romaine lettuce with Caesar dressing, croutons, and parmesan.",
        price: 9.99,
        category: "Salad",
        image: "https://images.unsplash.com/photo-1546793665-c74683f339c1?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60"
    },
    {
        id: 4,
        name: "Veggie Wrap",
        description: "A healthy wrap filled with fresh vegetables and hummus.",
        price: 8.99,
        category: "Wraps",
        image: "https://s.lightorangebean.com/media/20240914152454/Fresh-Veggie-Hummus-Wrap_-done.png"
    },
    {
        id: 5,
        name: "Chicken Wings",
        description: "Spicy chicken wings served with your choice of sauce.",
        price: 10.99,
        category: "Appetizers",
        image: "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60"
    },
    {
        id: 6,
        name: "Chocolate Cake",
        description: "Rich and moist chocolate cake with chocolate frosting.",
        price: 5.99,
        category: "Desserts",
        image: "https://images.unsplash.com/photo-1578985545062-69928b1d9587?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60"
    },
    {
        id: 7,
        name: "Fruit Salad",
        description: "A refreshing mix of seasonal fruits.",
        price: 6.99,
        category: "Desserts",
        image: "https://www.modernhoney.com/wp-content/uploads/2023/05/Fruit-Salad-10.jpg"
    },
    {
        id: 8,
        name: "Iced Tea",
        description: "Chilled iced tea served with lemon.",
        price: 2.99,
        category: "Beverages",
        image: "https://images.unsplash.com/photo-1597318181409-cf64d0b5d8a2?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60"
    },
    {
        id: 9,
        name: "Smoothie",
        description: "A blended drink made with fresh fruits and yogurt.",
        price: 4.99,
        category: "Beverages",
        image: "https://images.unsplash.com/photo-1505252585461-04db1eb84625?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60"
    },
    {
        id: 10,
        name: "Beef Burger",
        description: "Juicy beef burger with lettuce, tomato, and cheese.",
        price: 11.99,
        category: "Burgers",
        image: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60"
    }
];

const menuContainer = document.querySelector('.menu-items');

menuItems.forEach(item => {
    const menuItem = document.createElement('div');
    menuItem.classList.add('menu-item');

    const image = document.createElement('img');
    image.src = item.image;
    image.alt = item.name;

    const name = document.createElement('h3');
    name.textContent = item.name;

    const description = document.createElement('p');
    description.textContent = item.description;

    const price = document.createElement('p');
    price.classList.add('price');
    price.textContent = `$${item.price.toFixed(2)}`;

    menuItem.appendChild(image);
    menuItem.appendChild(name);
    menuItem.appendChild(description);
    menuItem.appendChild(price);

    menuContainer.appendChild(menuItem);
});