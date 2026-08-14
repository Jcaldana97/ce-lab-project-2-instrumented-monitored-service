# app/server.py
import structlog
from flask import Flask, request
import uuid
import time
 
# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.WriteLoggerFactory(file=open("application.log", "a")),
)
 
logger = structlog.get_logger()
app = Flask(__name__)
 
@app.route('/')
def index():
    correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
    
    logger.info(
        "request_received",
        correlation_id=correlation_id,
        path="/",
        method=request.method,
        ip=request.remote_addr
    )
    
    return {"message": "Hello World", "correlation_id": correlation_id}
 
@app.route('/health')
def health():
    logger.info("health_check", status="healthy")
    return {"status": "healthy"}
 
@app.route('/order', methods=['POST'])
def create_order():
    correlation_id = str(uuid.uuid4())
    data = request.get_json()

    order_id = f"ord-{uuid.uuid4().hex[:8]}"
    
    logger.info(
        "order_created",
        correlation_id=correlation_id,
        order_id=order_id,
        cart_id=data.get('cart_id'),
        amount=data.get('amount', 0),
        items=data.get('items', 0),
        user_id=data.get('user_id')
    )
    
    return {"status": "created", "order_id": order_id, "correlation_id": correlation_id}

@app.route('/cart', methods=['POST'])
def create_cart():
    correlation_id = str(uuid.uuid4())
    data = request.get_json()

    cart_id = f"cart-{uuid.uuid4().hex[:8]}"

    logger.info(
        "cart_created",
        correlation_id=correlation_id,
        cart_id=cart_id,
        user_id=data.get('user_id'),
        items=data.get('items', 0)
    )

    return {
        "status": "created",
        "cart_id": cart_id,
        "correlation_id": correlation_id
    }
 
@app.route('/error')
def error():
    logger.error("request_failed", path="/error", error="simulated failure")
    return {"status": "error"}, 500
 
if __name__ == '__main__':
    logger.info("application_started", port=5000)
    app.run(host='0.0.0.0', port=5000)