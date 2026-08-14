# app/server.py

import structlog
from flask import Flask, request, g, render_template_string
import uuid
import time
import threading
import boto3


# =========================================================
# Configuration
# =========================================================

AWS_REGION = "eu-east-1"

# Short timeout for demonstration/testing.
# Change this to e.g. 1800 for 30 minutes in production.
CART_ABANDONMENT_TIMEOUT = 60


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
# CloudWatch
# =========================================================

cloudwatch = boto3.client(
    "cloudwatch",
    region_name=AWS_REGION
)


# =========================================================
# In-memory cart storage
#
# Demo only. Use DynamoDB/Redis in production.
# =========================================================

carts = {}

cart_lock = threading.Lock()


# =========================================================
# Request timing
# =========================================================

@app.before_request
def start_timer():
    g.start_time = time.time()


@app.after_request
def record_request_latency(response):

    duration_ms = (time.time() - g.start_time) * 1000

    logger.info(
        "request_completed",
        path=request.path,
        method=request.method,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2)
    )

    return response


# =========================================================
# CloudWatch metric
# =========================================================

def publish_cart_abandonment_metric(abandoned, total_carts):

    if total_carts == 0:
        abandonment_rate = 0
    else:
        abandonment_rate = (
            abandoned / total_carts
        ) * 100

    cloudwatch.put_metric_data(
        Namespace="OrderService",
        MetricData=[
            {
                "MetricName": "CartAbandonmentRate",
                "Value": abandonment_rate,
                "Unit": "Percent",
                "Dimensions": [
                    {
                        "Name": "Service",
                        "Value": "OrderService"
                    }
                ]
            }
        ]
    )

    logger.info(
        "cart_abandonment_metric",
        abandoned=abandoned,
        total_carts=total_carts,
        abandonment_rate=round(abandonment_rate, 2)
    )

    return abandonment_rate


# =========================================================
# UI
# =========================================================

UI = """
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Order Service</title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            color: #222;
        }

        header {
            background: #1f2937;
            color: white;
            padding: 25px;
        }

        header h1 {
            margin: 0;
        }

        header p {
            margin-bottom: 0;
            color: #d1d5db;
        }

        .container {
            max-width: 1100px;
            margin: 30px auto;
            padding: 0 20px;
        }

        .grid {
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .card {
            background: white;
            border-radius: 10px;
            padding: 22px;
            box-shadow:
                0 2px 8px rgba(0,0,0,0.08);
        }

        .card h2 {
            margin-top: 0;
        }

        label {
            display: block;
            margin-top: 12px;
            font-weight: bold;
        }

        input {
            width: 100%;
            padding: 10px;
            margin-top: 5px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }

        button {
            margin-top: 15px;
            padding: 10px 16px;
            border: none;
            border-radius: 5px;
            background: #2563eb;
            color: white;
            cursor: pointer;
            font-size: 14px;
        }

        button:hover {
            background: #1d4ed8;
        }

        button.secondary {
            background: #6b7280;
        }

        button.danger {
            background: #dc2626;
        }

        .result {
            margin-top: 15px;
            padding: 12px;
            background: #f3f4f6;
            border-radius: 5px;
            white-space: pre-wrap;
            word-break: break-word;
            font-family: monospace;
            font-size: 13px;
        }

        .metric {
            font-size: 30px;
            font-weight: bold;
            margin: 15px 0;
        }

        .status {
            padding: 8px 12px;
            border-radius: 5px;
            display: inline-block;
            background: #dcfce7;
            color: #166534;
        }

        .warning {
            background: #fef3c7;
            color: #92400e;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
        }

        footer {
            text-align: center;
            padding: 30px;
            color: #6b7280;
        }

    </style>

</head>

<body>

<header>

    <h1>Order Service</h1>

    <p>
        Customer interface for carts, orders and monitoring
    </p>

</header>


<div class="container">

    <div class="grid">


        <!-- CREATE CART -->

        <div class="card">

            <h2>🛒 Create Cart</h2>

            <label>User ID</label>

            <input
                id="userId"
                type="text"
                value="user-demo"
            >

            <label>Number of Items</label>

            <input
                id="items"
                type="number"
                value="2"
                min="1"
            >

            <button onclick="createCart()">
                Create Cart
            </button>

            <div id="cartResult"
                 class="result">
                No cart created yet.
            </div>

        </div>


        <!-- COMPLETE ORDER -->

        <div class="card">

            <h2>💳 Complete Order</h2>

            <label>Cart ID</label>

            <input
                id="cartId"
                type="text"
                placeholder="cart-xxxxxxxx"
            >

            <label>Amount</label>

            <input
                id="amount"
                type="number"
                value="49.99"
                step="0.01"
            >

            <button onclick="createOrder()">
                Complete Order
            </button>

            <div id="orderResult"
                 class="result">
                No order created yet.
            </div>

        </div>


        <!-- CART STATUS -->

        <div class="card">

            <h2>📊 Cart Monitoring</h2>

            <p>
                Current abandonment timeout:
                <strong>60 seconds</strong>
            </p>

            <button onclick="checkAbandonment()">
                Evaluate Carts
            </button>

            <div id="abandonmentResult"
                 class="result">
                No metric evaluation yet.
            </div>

        </div>


        <!-- HEALTH -->

        <div class="card">

            <h2>❤️ Service Health</h2>

            <button onclick="checkHealth()">
                Check Health
            </button>

            <div id="healthResult"
                 class="result">
                No health check performed.
            </div>

        </div>


        <!-- ERROR TEST -->

        <div class="card">

            <h2>⚠️ Error Test</h2>

            <p>
                Generates a simulated HTTP 500 error.
            </p>

            <button
                class="danger"
                onclick="testError()">
                Generate Error
            </button>

            <div id="errorResult"
                 class="result">
                No error generated.
            </div>

        </div>


        <!-- USER GUIDE -->

        <div class="card">

            <h2>ℹ️ How to Test</h2>

            <ol>

                <li>Create a cart.</li>

                <li>
                    Copy the generated Cart ID.
                </li>

                <li>
                    Either complete the order,
                    or leave the cart untouched.
                </li>

                <li>
                    Wait 60 seconds for abandonment.
                </li>

                <li>
                    Click "Evaluate Carts".
                </li>

            </ol>

        </div>

    </div>


    <!-- RESULTS -->

    <div class="card" style="margin-top:20px">

        <h2>📈 Cart Abandonment Metric</h2>

        <div id="metricValue"
             class="metric">
            --
        </div>

        <p>
            CartAbandonmentRate
        </p>

    </div>

</div>


<footer>

    Order Service Demo &mdash;
    Flask + EC2 + CloudWatch

</footer>


<script>

async function createCart() {

    const userId =
        document.getElementById("userId").value;

    const items =
        parseInt(
            document.getElementById("items").value
        );

    const response = await fetch(
        "/cart",
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                user_id: userId,
                items: items
            })
        }
    );

    const data = await response.json();

    document.getElementById(
        "cartResult"
    ).textContent =
        JSON.stringify(data, null, 2);

    if (data.cart_id) {

        document.getElementById(
            "cartId"
        ).value = data.cart_id;
    }
}


async function createOrder() {

    const cartId =
        document.getElementById("cartId").value;

    const userId =
        document.getElementById("userId").value;

    const amount =
        parseFloat(
            document.getElementById("amount").value
        );

    const items =
        parseInt(
            document.getElementById("items").value
        );

    const response = await fetch(
        "/order",
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                cart_id: cartId,
                user_id: userId,
                amount: amount,
                items: items
            })
        }
    );

    const data = await response.json();

    document.getElementById(
        "orderResult"
    ).textContent =
        JSON.stringify(data, null, 2);
}


async function checkAbandonment() {

    const response = await fetch(
        "/metrics/cart-abandonment"
    );

    const data = await response.json();

    document.getElementById(
        "abandonmentResult"
    ).textContent =
        JSON.stringify(data, null, 2);

    document.getElementById(
        "metricValue"
    ).textContent =
        data.abandonment_rate_percent + "%";
}


async function checkHealth() {

    const response = await fetch(
        "/health"
    );

    const data = await response.json();

    document.getElementById(
        "healthResult"
    ).textContent =
        JSON.stringify(data, null, 2);
}


async function testError() {

    const response = await fetch(
        "/error"
    );

    const data = await response.json();

    document.getElementById(
        "errorResult"
    ).textContent =
        "HTTP " +
        response.status +
        "\\n" +
        JSON.stringify(data, null, 2);
}

</script>

</body>

</html>
"""


# =========================================================
# UI route
# =========================================================

@app.route("/ui")
def ui():

    return render_template_string(UI)


# =========================================================
# API: Home
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
# API: Health
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
# API: Create Cart
# =========================================================

@app.route("/cart", methods=["POST"])
def create_cart():

    correlation_id = str(uuid.uuid4())

    data = request.get_json() or {}

    cart_id = f"cart-{uuid.uuid4().hex[:8]}"

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
# API: Create Order
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
                "message":
                    f"cart is already {cart['status']}"
            }, 400

        cart["status"] = "completed"
        cart["updated_at"] = time.time()

    order_id = f"ord-{uuid.uuid4().hex[:8]}"

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
# API: Cart abandonment metric
# =========================================================

@app.route("/metrics/cart-abandonment")
def cart_abandonment_metric():

    now = time.time()

    with cart_lock:

        for cart in carts.values():

            if (
                cart["status"] == "active"
                and
                now - cart["updated_at"]
                >= CART_ABANDONMENT_TIMEOUT
            ):

                cart["status"] = "abandoned"

                logger.info(
                    "cart_abandoned",
                    cart_id=cart["cart_id"],
                    user_id=cart["user_id"]
                )

        total_carts = len(carts)

        abandoned = sum(
            1
            for cart in carts.values()
            if cart["status"] == "abandoned"
        )

    rate = publish_cart_abandonment_metric(
        abandoned,
        total_carts
    )

    return {
        "metric": "CartAbandonmentRate",
        "abandoned_carts": abandoned,
        "total_carts": total_carts,
        "abandonment_rate_percent": round(rate, 2)
    }


# =========================================================
# API: Simulated error
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
# Start application
# =========================================================

if __name__ == "__main__":

    logger.info(
        "application_started",
        port=5000
    )

    app.run(
        host="0.0.0.0",
        port=5000
    )