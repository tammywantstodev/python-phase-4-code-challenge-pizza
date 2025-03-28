#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route("/restaurants")
def get_restaurants():
    restaurants=db.session.query(Restaurant).all()
    response=[
        restaurant.to_dict(only=("id", "name", "address")) for restaurant in restaurants
    ]
    return jsonify(response)

@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant_by_id(id):
    restaurant= db.session.query(Restaurant).filter_by(id=id).first()
    if restaurant:
        return jsonify({
            'address':restaurant.address,
            'id':restaurant.id,
            'name':restaurant.name,
            "restaurant_pizzas": [
                {
                    "id": rp.id,
                    "pizza": rp.pizza.to_dict(only=("id", "name", "ingredients")),
                    "pizza_id": rp.pizza_id,
                    "price": rp.price,
                    "restaurant_id": rp.restaurant_id
                } for rp in restaurant.restaurant_pizzas
            ]
        })
    else:
        return jsonify({"error": "Restaurant not found"}), 404
    
@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = db.session.query(Restaurant).filter_by(id=id).first()
    
    if restaurant:
        for restaurant_pizza in restaurant.restaurant_pizzas:
            db.session.delete(restaurant_pizza)
        
        db.session.delete(restaurant)
        db.session.commit()
        
        return '', 204
    
    else:
        return jsonify({"error": "Restaurant not found"}), 404

@app.route('/pizzas', methods=["GET"])  
def get_pizzas():
    pizzas=db.session.query(Pizza).all()
    response=[
        pizza.to_dict(only=("id", "ingredients", "name")) for pizza in pizzas
    ]
    return jsonify(response)
@app.route('/restaurant_pizzas', methods=["POST"])
def post_restaurant_pizzas():
    data = request.get_json()

    price = data.get("price")
    pizza_id = data.get("pizza_id")
    restaurant_id = data.get("restaurant_id")

    errors = []  

    pizza = db.session.query(Pizza).filter_by(id=pizza_id).first()
    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).first()

    if not pizza:
        errors.append("Invalid pizza_id: Pizza not found")
    if not restaurant:
        errors.append("Invalid restaurant_id: Restaurant not found")

    if price is None or not isinstance(price, (int, float)) or price <= 0:
        errors.append("Price must be a positive number")

    if errors:
        return jsonify({"errors": errors}), 400

    new_restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
    db.session.add(new_restaurant_pizza)
    db.session.commit()

    return jsonify({
        "id": new_restaurant_pizza.id,
        "pizza": pizza.to_dict(only=("id", "name", "ingredients")),
        "pizza_id": new_restaurant_pizza.pizza_id,
        "price": new_restaurant_pizza.price,
        "restaurant": restaurant.to_dict(only=("id", "name", "address")),
        "restaurant_id": new_restaurant_pizza.restaurant_id
    }), 201