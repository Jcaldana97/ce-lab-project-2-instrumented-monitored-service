# Project 2: Instrumented & Monitored Cloud Service

## Architecture Overview

A general overview of the architecture is shown in the following picture: 

![Architecture Diagram](docs/architecture/architecture-diagram.png)

## Deployed workload with structured logging

The server runs the application _server.py_ found in the location _app/_. In order to identify each event on the server, a correlation ID generation is implemented. When a requests is received, the corresponding actions are performed, and the results are sent to the logs with a correlation ID as the first attribute. 

To create a correlation ID, the _UUID Generator_ package is imported and used to generate a unique id for each event. The Correlation ID looks as follows: 

```bash
Correlation ID: c303282d-f2e6-46ca-a04a-35d3d873712d
```

For each event, the logger stores the relevant data that the endpoint manages and stores the Correlation ID as the first attribute. For example, for the creation of a cart, the logger stores the following information: 

```bash
    logger.info(
        "order_created",
        correlation_id=correlation_id,
        order_id=order_id,
        cart_id=cart_id,
        amount=data.get("amount", 0),
        items=data.get("items", 0),
        user_id=data.get("user_id")
    )
```

## Custom metrics instrumentation

### Custom metrics - Technical 

- **Memory Utilization:** To get the memory utilization, a metric filter is created to count the matching lines in the log group. This metric filter is defined in the file _cwagent-metrics.json_. For this metric, the measurements used are collected with the key *mem_used_percent*. 
- **Disk Space:**  The disk space used is extracted from the logs via CW Agent. The mesurements are collected and stored with the key *user_percent*. This key encapsulates some other measurements; to access to the disk measurements, the key *disk_user_percent* is used in the dashboard or alerts. 
- **Application Error Rate:** This metric filters the log lines and turns them into a numeric metric: every line in /aws/application/api matching $.level = "error" publishes a 1 to Application/ErrorCount, which the alarm then sums.
- **Order Rate:** This metric filters the log lines and turns them into a numeric metric: every line in /aws/application/api matching $.event = "order_created" publishes a 1 to Application/OrderCount, which will be displayed in the dashboard. 

### Custom metrics - Bussiness

- **Total Carts:** This metric extracts the total amount of carts that have been created. 
- **Abandoned Carts:** This metrics extracts the number of abandoned carts. 
- **Completed Carts:** This metric extracts the number of completed carts. 
- **Cart Abandonment Rate:** This metrics extracts the rate of cart abandonment already calculated in the application. 


## CloudWatch dashboards with key metrics

The design of the dashboard is shown in the following picture: 

![Dashboard Design](docs/architecture/dashboard-design.png)

The configuration of the dashboard can be found in _config/dashboard.json_.

## Tiered alerting system

### Alarm 1: CPU Utilization 

**Warning Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 2 (10 minutes total)
- Threshold: 70%
- Justification: CPU Usage is high but in a threshold where an action can still be performed.  
- Comparison: GreaterThan

**Critical Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 1
- Threshold: 90%
- Justification: CPU Usage is almost reaching 100%, immediate action must be performed.  
- Comparison: GreaterThan


### Alarm 2: Memory Utilization

**Warning Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 2 (10 minutes total)
- Threshold: 70%
- Justification: Memory Usage is high but in a threshold where an action can still be performed.  
- Comparison: GreaterThan


**Critical Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 1
- Threshold: 90%
- Justification: Memory Usage is almost reaching 100%, immediate action must be performed.  
- Comparison: GreaterThan

### Alarm 3: Disk Space

**Warning Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 2 (10 minutes total)
- Threshold: 70%
- Justification: Disk Space is running out but in a threshold where an action can still be performed.  
- Comparison: GreaterThan

**Critical Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 1
- Threshold: 90%
- Justification: Disk Space is almost full, immediate action must be performed.  
- Comparison: GreaterThan

### Alarm 4: Application Error Rate Alarm 

- Period: 300 seconds (5 minutes)
- Evaluation periods: 1
- Threshold: 10
- Justification: Having an error rate of 2 errors per minute is sufficient to consider that there is an issue.  
- Comparison: GreaterThan

## Alarm 5: Application Load Balancer Response Time Alert

This alarm is triggered when the Load Balancer response exceeds 500 ms.



## Root cause analysis of an injected failure

### RED Method Analysis

**Rate (Traffic)**

- Normal: 25 req/min
- Incident: 632 req/min - See Health Dashboard Error Rate
- **Finding: 10x traffic increase**
 
**Errors**

- Normal: 0.1%
- Incident: 35.0% during the incident - See Golden Signals Error Rate
- **Finding: 70x error increase**

**Duration (Latency)**

- Normal P95: 200ms
- Incident P95: 2,000ms
- **Finding: 10x latency increase**

**Conclusion**

All three RED signals elevated. Significant performance degradation.
Primary symptom: High latency (10x increase)

### USE Method Summary

**CPU**

- 🔴 Utilization: 95% (abnormal)
- 🔴 Saturation: Abormal
- 🔴 Errors: Timeout errors

**ROOT CAUSE IDENTIFIED: Ec2 instance undersized for the workload, or an unexpected traffic/application workload spike is exhausting available CPU**

## Incident summary 

- **Incident:** API latency increased from 200ms (P95) to 2,000ms (P95)  
- **Impact:** 2,500 users experienced slow page loads, 35% error rate  
- **Duration:** 60 minutes (17:00-18:00 UTC, Aug 14, 2024)  
- **Root Cause:**  Unexpected traffic/application workload 
- **Status:** Resolved

| Time (UTC) | Event |
|------------|-------|
| 14:00 | CloudWatch alarm triggered: High latency detected |
| 14:05 | CloudWatch alarm triggered: High Error Rate detected |
| 14:10 | Investigation started using RED method |
| 14:15 | Confirmed elevated error rate and latency |
| 14:20 | USE method applied to resources |
| 14:25 | Identified EC2 CPU Usage at 96% |
| 14:30 | ROOT CAUSE: Unexpected traffic/application workload |
| 14:35 | Immediate fix: Increase the number of EC2 instances in the ALB |
| 14:40 | Service began recovering |
| 14:50 | Latency returned to normal |
| 15:00 | Incident closed |
