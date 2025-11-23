from flask import Flask, request, jsonify
import os
import logging
from datetime import datetime , timezone

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory inventory storage
inventory = {
    "P001": {
        "product_id": "P001",
        "name": "Laptop",
        "price": 999.99,
        "available_quantity": 50,
        "reserved_quantity": 0
    },
    "P002": {
        "product_id": "P002",
        "name": "Wireless Mouse",
        "price": 29.99,
        "available_quantity": 200,
        "reserved_quantity": 0
    },
    "P003": {
        "product_id": "P003",
        "name": "USB-C Cable",
        "price": 15.99,
        "available_quantity": 500,
        "reserved_quantity": 0
    },
    "P004": {
        "product_id": "P004",
        "name": "Mechanical Keyboard",
        "price": 149.99,
        "available_quantity": 30,
        "reserved_quantity": 0
    }
}

# Healthcheck Route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "inventory-service"}), 200


# List all producsts and their inventory levels
@app.route('/inventory', methods=['GET'])
def list_inventory():
    return jsonify({
        "products": list(inventory.values()),
        "total_products": len(inventory)
    }), 200


# Get inventory details for a specific product
@app.route('/inventory/<product_id>', methods=['GET'])
def get_product(product_id):
    product = inventory.get(product_id)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify(product), 200



# Inventory Check for a product
@app.route('/inventory/check', methods=['POST'])
def check_availability():
    try:
        data = request.get_json()
        
        if not data or 'product_id' not in data or 'quantity' not in data:
            return jsonify({"error": "Missing required fields: product_id, quantity"}), 400
        
        product_id = data['product_id']
        requested_quantity = data['quantity']
        
        if requested_quantity <= 0:
            return jsonify({"error": "Quantity must be positive"}), 400
        
        product = inventory.get(product_id)
        
        if not product:
            return jsonify({
                "available": False,
                "error": "Product not found",
                "product_id": product_id
            }), 404
        
        available_quantity = product['available_quantity']
        is_available = available_quantity >= requested_quantity
        
        logger.info(f"Availability check for {product_id}: requested={requested_quantity}, available={available_quantity}, result={is_available}")
        
        return jsonify({
            "available": is_available,
            "product_id": product_id,
            "requested_quantity": requested_quantity,
            "available_quantity": available_quantity,
            "price": product['price']
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return jsonify({"error": "Internal server error"}), 500



# Reserve inventory for an order
@app.route('/inventory/reserve', methods=['POST'])
def reserve_inventory():
    try:
        data = request.get_json()
        
        if not data or 'product_id' not in data or 'quantity' not in data:
            return jsonify({"error": "Missing required fields: product_id, quantity"}), 400
        
        product_id = data['product_id']
        quantity = data['quantity']
        
        if quantity <= 0:
            return jsonify({"error": "Quantity must be positive"}), 400
        
        product = inventory.get(product_id)
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        if product['available_quantity'] < quantity:
            return jsonify({
                "error": "Insufficient inventory",
                "requested": quantity,
                "available": product['available_quantity']
            }), 400
        
        # Reserve inventory
        product['available_quantity'] -= quantity
        product['reserved_quantity'] += quantity
        product['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Reserved {quantity} units of {product_id}. New available: {product['available_quantity']}")
        
        return jsonify({
            "success": True,
            "product_id": product_id,
            "reserved_quantity": quantity,
            "remaining_available": product['available_quantity']
        }), 200
        
    except Exception as e:
        logger.error(f"Error reserving inventory: {e}")
        return jsonify({"error": "Internal server error"}), 500



# Release reserved inventory
@app.route('/inventory/release', methods=['POST'])
def release_inventory():
    try:
        data = request.get_json()
        
        if not data or 'product_id' not in data or 'quantity' not in data:
            return jsonify({"error": "Missing required fields: product_id, quantity"}), 400
        
        product_id = data['product_id']
        quantity = data['quantity']
        
        if quantity <= 0:
            return jsonify({"error": "Quantity must be positive"}), 400
        
        product = inventory.get(product_id)
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        # Release inventory back to available
        product['available_quantity'] += quantity
        product['reserved_quantity'] = max(0, product['reserved_quantity'] - quantity)
        product['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Released {quantity} units of {product_id}. New available: {product['available_quantity']}")
        
        return jsonify({
            "success": True,
            "product_id": product_id,
            "released_quantity": quantity,
            "available_quantity": product['available_quantity']
        }), 200
        
    except Exception as e:
        logger.error(f"Error releasing inventory: {e}")
        return jsonify({"error": "Internal server error"}), 500



# Add inventory to a product
@app.route('/inventory/<product_id>/restock', methods=['POST'])
def restock_product(product_id):
    try:
        data = request.get_json()
        
        if not data or 'quantity' not in data:
            return jsonify({"error": "Missing required field: quantity"}), 400
        
        quantity = data['quantity']
        
        if quantity <= 0:
            return jsonify({"error": "Quantity must be positive"}), 400
        
        product = inventory.get(product_id)
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        product['available_quantity'] += quantity
        product['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Restocked {quantity} units of {product_id}. New available: {product['available_quantity']}")
        
        return jsonify({
            "success": True,
            "product_id": product_id,
            "restocked_quantity": quantity,
            "new_available_quantity": product['available_quantity']
        }), 200
        
    except Exception as e:
        logger.error(f"Error restocking inventory: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)