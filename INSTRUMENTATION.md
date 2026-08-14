# Instrumentation 

## Logging strategy

## Custom metrics - Technical 

### Memory Utilization

To get the memory utilization, a metric filter is created to count the matching lines in the log group. This metric filter is defined in the file _cwagent-metrics.json_. For this metric, the measurements used are collected with the key *mem_used_percent*. After the json file is added to the server, the metrics are appended using the following command: 

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a append-config -m ec2 -s \
  -c file:/tmp/cwagent-metrics.json
```

### Disk Space 

Similarly to the memory utilization, the disk space used is extracted from the logs via CW Agent. The mesurements are collected and stored with the key *user_percent*. This key encapsulates some other measurements; to access to the disk measurements, the key *disk_user_percent* is used in the dashboard or alerts. 

### Application Error Rate

This metric filters the log lines and turns them into a numeric metric: every line in /aws/application/api matching $.level = "error" publishes a 1 to Application/ErrorCount, which the alarm then sums.

```bash
aws logs put-metric-filter \
  --log-group-name /aws/application/api \
  --filter-name ErrorCount \
  --filter-pattern '{ $.level = "error" }' \
  --metric-transformations \
    metricName=ErrorCount,metricNamespace=Application,metricValue=1
```

### Order Rate

This metric filters the log lines and turns them into a numeric metric: every line in /aws/application/api matching $.event = "order_created" publishes a 1 to Application/OrderCount, which will be displayed in the dashboard. 

```bash
aws logs put-metric-filter \
  --log-group-name /aws/application/api \
  --filter-name OrderCount \
  --filter-pattern '{ $.event = "order_created" }' \
  --metric-transformations \
    metricName=OrderCount,metricNamespace=Application,metricValue=1
```

## Custom metrics - Bussiness

The server was extended for the user to create carts for their purchases. The interaction of the user with the application is logged, the information may look as follows: 

```bash
{
    "event": "cart_abandonment_metric",
    "metric_name": "CartAbandonmentRate",
    "metric_value": 40.0,
    "total_carts": 10,
    "abandoned_carts": 4,
    "completed_carts": 6,
    "active_carts": 0
}
```

This information helps to understand the user experience in terms of bussiness and detect possible pitfalls for them with the application. 

### Total Carts

This metric extracts the total amount of carts that have been created. 

```bash
aws logs put-metric-filter \
  --log-group-name /aws/application/api \
  --filter-name "CartTotalCarts" \
  --filter-pattern '{ $.metric_name = "CartAbandonmentRate" && $.total_carts = * }' \
  --metric-transformations \
    metricName=TotalCarts,metricNamespace=OrderService,metricValue='$.total_carts',unit=Count
```

### Abandoned Carts

This metrics extracts the number of abandoned carts. 

```bash 
aws logs put-metric-filter \
  --log-group-name /aws/application/api \
  --filter-name "CartAbandonedCarts" \
  --filter-pattern '{ $.metric_name = "CartAbandonmentRate" && $.abandoned_carts = * }' \
  --metric-transformations \
    metricName=AbandonedCarts,metricNamespace=OrderService,metricValue='$.abandoned_carts',unit=Count
```

### Completed Carts

This metric extracts the number of completed carts. 

```bash
aws logs put-metric-filter \
  --log-group-name /aws/application/api \
  --filter-name "CartCompletedCarts" \
  --filter-pattern '{ $.metric_name = "CartAbandonmentRate" && $.completed_carts = * }' \
  --metric-transformations \
    metricName=CompletedCarts,metricNamespace=OrderService,metricValue='$.completed_carts',unit=Count
```

### Active Carts

This metric extracts the number of active carts in the service. 

```bash
aws logs put-metric-filter \
  --log-group-name /aws/application/api \
  --filter-name "CartActiveCarts" \
  --filter-pattern '{ $.metric_name = "CartAbandonmentRate" && $.active_carts = * }' \
  --metric-transformations \
    metricName=ActiveCarts,metricNamespace=OrderService,metricValue='$.active_carts',unit=Count
```

### Cart Abandonment Rate

This metrics extracts the rate of cart abandonment already calculated in the application. 

```bash
aws logs put-metric-filter \
  --log-group-name /aws/application/api \
  --filter-name "CartAbandonmentRate" \
  --filter-pattern '{ $.metric_name = "CartAbandonmentRate" && $.abandonment_rate = * }' \
  --metric-transformations \
    metricName=CartAbandonmentRate,metricNamespace=OrderService,metricValue='$.abandonment_rate',unit=Percent
```

## Correlation ID implementation