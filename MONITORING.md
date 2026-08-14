# Monitoring

## Dashboard design and rationale

The design of the dashboard is shown in the following picture: 

![Dashboard Design](architecture/docs/dashboard-design.png)

To make any updates, refer to the *dashboard.json* file and run the following command after every update. 

```bash
aws cloudwatch put-dashboard \
  --dashboard-name Project2_WebTierMonitoring \
  --dashboard-body file://dashboard.json
```


## Golden Signals implementation

### Trafic - Request Rate

### Errors - HTTP Status Codes

### Latency - Response Time Percentiles

### Saturation - Target Health 

## Widget explanations

### Web Tier Health Dashboard 

- Current Request Rate
- Error Rate (%)
- P95 Latency (ms) 
- Healthy Targets 


### Golden Signals

- **Trafic - Request Rate:**
- **Errors - HTTP Status Codes:**
- **Latency - Response Time Percentiles:**
- **Saturation - Target Health:**

### EC2 Resource Utilization

### Correlation View 


## How to use dashboard for troubleshooting



