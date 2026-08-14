import structlog
from flask import Flask, request, g, render_template
import uuid
import time
import threading


# =========================================================
# Configuration
# =========================================================

# A cart is considered abandoned after 60 seconds.
# Change this to 1800 for 30 minutes in production.
CART_ABANDONMENT_TIMEOUT = 60

# Run cart monitoring every 30 seconds.
CART_MONITORING_INTERVAL = 30


# =========================================================
# Structured logging
# =========================================================

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.WriteLoggerFactory(
        file=open("application.log", "a")
    ),
)

logger = structlog.get_logger()


# =========================================================
# Flask
# =========================================================

app = Flask(__name__)


# =========================================================
# In-memory cart storage
#
# Demo only.
# A production application should use DynamoDB, Redis,
# or another persistent/shared datastore.
# =========================================================

carts = {}

cart_lock = threading.Lock()


# =========================================================
# Cart monitoring
# =========================================================

def monitor_carts():

    while True:

        try:

            now = time.time()

            newly_abandoned = 0

            with cart_lock:

                for cart in carts.values():

                    if (
                        cart["status"] == "active"
                        and
                        now - cart["updated_at"]
                        >= CART_ABANDONMENT_TIMEOUT
                    ):

                        cart["status"] = "abandoned"

                        newly_abandoned += 1

                        logger.info(
                            "cart_abandoned",
                            cart_id=cart["cart_id"],
                            user_id=cart["user_id"]
                        )

                total_carts = len(carts)

                abandoned_carts = sum(
                    1
                    for cart in carts.values()
                    if cart["status"] == "abandoned"
                )

                completed_carts = sum(
                    1
                    for cart in carts.values()
                    if cart["status"] == "completed"
                )

            if total_carts == 0:

                abandonment_rate = 0

            else:

                abandonment_rate = (
                    abandoned_carts / total_carts
                ) * 100

            logger.info(
                "cart_abandonment_metric",
                metric_name="CartAbandonmentRate",
                total_carts=total_carts,
                newly_abandoned=newly_abandoned,
                abandoned_carts=abandoned_carts,
                completed_carts=completed_carts,
                active_carts=total_carts
                    - abandoned_carts
                    - completed_carts,
                abandonment_rate=round(
                    abandonment_rate,
                    2
                )
            )

        except Exception as exc:

            logger.error(
                "cart_monitoring_failed",
                error=str(exc)
            )

        time.sleep(CART_MONITORING_INTERVAL)


# =========================================================
# Start background cart monitoring
# =========================================================

monitor_thread = threading.Thread(
    target=monitor_carts,
    daemon=True
)

monitor_thread.start()


# =========================================================
# Request timing
# =========================================================

@app.before_request
def start_timer():

    g.start_time = time.time()


@app.after_request
def record_request_latency(response):

    duration_ms = (
        time.time() - g.start_time
    ) * 1000

    logger.info(
        "request_completed",
        path=request.path,
        method=request.method,
        status_code=response.status_code,
        duration_ms=round(
            duration_ms,
            2
        )
    )

    return response


# =========================================================
# UI
# =========================================================

@app.route("/ui")
def ui():

    return render_template(
        "index.html"
    )


# =========================================================
# Home
# =========================================================

@app.route("/")
def index():

    correlation_id = request.headers.get(
        "X-Correlation-ID",
        str(uuid.uuid4())
    )

    logger.info(
        "request_received",
        correlation_id=correlation_id,
        path="/",
        method=request.method,
        ip=request.remote_addr
    )

    return {
        "message": "Hello World",
        "correlation_id": correlation_id
    }


# =========================================================
# Health
# =========================================================

@app.route("/health")
def health():

    logger.info(
        "health_check",
        status="healthy"
    )

    return {
        "status": "healthy"
    }


# =========================================================
# Create Cart
# =========================================================

@app.route("/cart", methods=["POST"])
def create_cart():

    correlation_id = str(uuid.uuid4())

    data = request.get_json() or {}

    cart_id = (
        f"cart-{uuid.uuid4().hex[:8]}"
    )

    now = time.time()

    cart = {
        "cart_id": cart_id,
        "user_id": data.get("user_id"),
        "items": data.get("items", 0),
        "created_at": now,
        "updated_at": now,
        "status": "active"
    }

    with cart_lock:

        carts[cart_id] = cart

    logger.info(
        "cart_created",
        correlation_id=correlation_id,
        cart_id=cart_id,
        user_id=cart["user_id"],
        items=cart["items"]
    )

    return {
        "status": "created",
        "cart_id": cart_id,
        "correlation_id": correlation_id
    }, 201


# =========================================================
# Create Order
# =========================================================

@app.route("/order", methods=["POST"])
def create_order():

    correlation_id = str(uuid.uuid4())

    data = request.get_json() or {}

    cart_id = data.get("cart_id")

    if not cart_id:

        return {
            "status": "error",
            "message": "cart_id is required"
        }, 400

    with cart_lock:

        cart = carts.get(cart_id)

        if not cart:

            return {
                "status": "error",
                "message": "cart not found"
            }, 404

        if cart["status"] != "active":

            return {
                "status": "error",
                "message": (
                    f"cart is already "
                    f"{cart['status']}"
                )
            }, 400

        cart["status"] = "completed"

        cart["updated_at"] = time.time()

    order_id = (
        f"ord-{uuid.uuid4().hex[:8]}"
    )

    logger.info(
        "order_created",
        correlation_id=correlation_id,
        order_id=order_id,
        cart_id=cart_id,
        amount=data.get("amount", 0),
        items=data.get("items", 0),
        user_id=data.get("user_id")
    )

    return {
        "status": "created",
        "order_id": order_id,
        "cart_id": cart_id,
        "correlation_id": correlation_id
    }, 201


# =========================================================
# Cart status / metric endpoint
#
# The background thread does the actual monitoring.
# This endpoint simply returns the current state.
# =========================================================

@app.route("/metrics/cart-abandonment")
def cart_abandonment_metric():

    with cart_lock:

        total_carts = len(carts)

        abandoned_carts = sum(
            1
            for cart in carts.values()
            if cart["status"] == "abandoned"
        )

        completed_carts = sum(
            1
            for cart in carts.values()
            if cart["status"] == "completed"
        )

        active_carts = sum(
            1
            for cart in carts.values()
            if cart["status"] == "active"
        )

    if total_carts == 0:

        abandonment_rate = 0

    else:

        abandonment_rate = (
            abandoned_carts / total_carts
        ) * 100

    return {
        "metric": "CartAbandonmentRate",
        "abandoned_carts": abandoned_carts,
        "completed_carts": completed_carts,
        "active_carts": active_carts,
        "total_carts": total_carts,
        "abandonment_rate_percent": round(
            abandonment_rate,
            2
        )
    }


# =========================================================
# Simulated Error
# =========================================================

@app.route("/error")
def error():

    logger.error(
        "request_failed",
        path="/error",
        error="simulated failure"
    )

    return {
        "status": "error"
    }, 500

# =========================================================
# Simulate slow requests
# =========================================================

@app.route("/slow")
def slow():

    delay = float(
        request.args.get("delay", "1")
    )

    logger.info(
        "slow_request",
        delay=delay
    )

    time.sleep(delay)

    return {
        "status": "ok",
        "delay": delay
    }


# =========================================================
# Start application
# =========================================================

if __name__ == "__main__":

    logger.info(
        "application_started",
        port=5000,
        cart_monitoring_interval=(
            CART_MONITORING_INTERVAL
        ),
        cart_abandonment_timeout=(
            CART_ABANDONMENT_TIMEOUT
        )
    )

    app.run(
        host="0.0.0.0",
        port=5000
    )