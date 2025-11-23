# Distributed Systems L4 - E-commerce Order Processing System

A distributed microservices application demonstrating service boundaries, inter-service communication, and Kubernetes deployment.

## Architecture

Two microservices:

- **Order Service** - Manages customer orders
- **Inventory Service** - Manages product inventory

**Technology Stack:**

- Python 3.12 + Flask
- Docker
- Kubernetes
- REST API communication

## Project Structure

```
.
├── order-service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── inventory-service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
└── k8s/
    ├── order-service.yaml
    └── inventory-service.yaml
```

## Prerequisites

- Python 3.12+
- Docker Desktop with Kubernetes enabled
- kubectl

## Setup & Deployment

### 1. Build Docker Images

```bash
docker build -t order-service:latest ./order-service
docker build -t inventory-service:latest ./inventory-service
```

### 2. Deploy to Kubernetes

```bash
kubectl apply -f k8s/inventory-service.yaml
kubectl apply -f k8s/order-service.yaml
```

### 3. Verify Deployment

```bash
kubectl get pods
kubectl get services
```

### 4. Test the Application

Create an order:

```bash
curl -X POST http://localhost:30000/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": "P001", "quantity": 2, "customer_id": "C123"}'
```

Check inventory:

```bash
kubectl port-forward service/inventory-service 5001:5001
curl http://localhost:5001/inventory/P001
```

## API Endpoints

### Order Service (Port 30000)

- `POST /orders` - Create order
- `GET /orders` - List all orders
- `GET /orders/{id}` - Get order details
- `DELETE /orders/{id}` - Cancel order

### Inventory Service (Port 5001)

- `GET /inventory` - List all products
- `GET /inventory/{id}` - Get product details
- `POST /inventory/check` - Check availability
- `POST /inventory/reserve` - Reserve inventory
- `POST /inventory/release` - Release inventory

## Key Features

- RESTful inter-service communication
- Kubernetes service discovery
- Health probes (liveness + readiness)
- Resource limits and constraints
- Error handling and validation

## Architecture Decisions

This project demonstrates key microservices concepts:

- Service boundary design based on business capabilities
- Synchronous REST communication for strong consistency
- Containerization and orchestration with K8s
- Trade-off analysis between coupling and consistency

## Important Note

The application uses **in-memory storage** for simplicity. In production, a shared database (PostgreSQL, MongoDB) would be required to support multiple replicas.

Currently deployed with 1 replica per service to maintain data consistency with in-memory storage.

## Cleanup

```bash
kubectl delete -f k8s/
```
