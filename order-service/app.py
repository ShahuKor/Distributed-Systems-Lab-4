from flask import Flask, request, jsonify
import requests
import os
import logging
from datetime import datetime, timezone

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In memory storage
orders = {}
order_counter = 1

INVENTORY_SERVICE_URL = os.getenv('INVENTORY_SERVICE_URL', 'http://inventory-service:5001')


#Health Check Route
@app.route('/health', methods=['GET'])

def health_check():
    return jsonify({"status": "healthy", "service": "order-service"}), 200

@app.route('/orders', methods=['POST'])

# Create New Order
def create_order():
    global order_counter
    
    try:
        data = request.get_json()
        
        if not data or 'product_id' not in data or 'quantity' not in data:
            return jsonify({"error": "Missing required fields: product_id, quantity"}), 400
        
        product_id = data['product_id']
        quantity = data['quantity']
        customer_id = data.get('customer_id', 'guest')
        
        # Synchronous REST call to Inventory Service to check availability
        logger.info(f"Checking inventory for product {product_id}, quantity {quantity}")
        
        try:
            inventory_response = requests.post(
                f"{INVENTORY_SERVICE_URL}/inventory/check",
                json={"product_id": product_id, "quantity": quantity},
                timeout=5
            )
            
            if inventory_response.status_code != 200:
                return jsonify({
                    "error": "Inventory check failed",
                    "details": inventory_response.json()
                }), 400
                
            inventory_data = inventory_response.json()
            
            if not inventory_data.get('available', False):
                return jsonify({
                    "error": "Insufficient inventory",
                    "available_quantity": inventory_data.get('available_quantity', 0)
                }), 400
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to communicate with Inventory Service: {e}")
            return jsonify({
                "error": "Service communication error",
                "message": "Unable to verify inventory availability"
            }), 503
        
        # Reserve inventory
        try:
            reserve_response = requests.post(
                f"{INVENTORY_SERVICE_URL}/inventory/reserve",
                json={"product_id": product_id, "quantity": quantity},
                timeout=5
            )
            
            if reserve_response.status_code != 200:
                return jsonify({
                    "error": "Failed to reserve inventory",
                    "details": reserve_response.json()
                }), 400
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to reserve inventory: {e}")
            return jsonify({
                "error": "Service communication error",
                "message": "Unable to reserve inventory"
            }), 503
        
        # Create order
        order_id = f"ORD{order_counter:04d}"
        order_counter += 1
        
        order = {
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
            "customer_id": customer_id,
            "status": "confirmed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_price": inventory_data.get('price', 0) * quantity
        }
        
        orders[order_id] = order
        logger.info(f"Order created successfully: {order_id}")
        
        return jsonify(order), 201
        
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Get Order details by ID
@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    order = orders.get(order_id)
    
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    return jsonify(order), 200

@app.route('/orders', methods=['GET'])

# List Orders
def list_orders():
    return jsonify({
        "orders": list(orders.values()),
        "total_count": len(orders)
    }), 200


# Cancel an order
@app.route('/orders/<order_id>', methods=['DELETE'])
def cancel_order(order_id):
    order = orders.get(order_id)
    
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    if order['status'] == 'cancelled':
        return jsonify({"message": "Order already cancelled"}), 200
    
    # inventory back to Inventory service
    try:
        release_response = requests.post(
            f"{INVENTORY_SERVICE_URL}/inventory/release",
            json={"product_id": order['product_id'], "quantity": order['quantity']},
            timeout=5
        )
        
        if release_response.status_code != 200:
            logger.warning(f"Failed to release inventory for order {order_id}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to communicate with Inventory Service: {e}")
    
    order['status'] = 'cancelled'
    order['cancelled_at'] = datetime.now(timezone.utc).isoformat()
    
    return jsonify(order), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)