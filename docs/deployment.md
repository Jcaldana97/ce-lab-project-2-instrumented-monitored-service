# Deployment 

## Server Setup

### Application with Structured Logging

Launch an EC2 Instance where the application will reside. Access to the EC2 Instance via SSH to install the application. 

```bash
ssh -i ~/bootcamp-week2-key.pem  ec2-user@3.231.57.212
```

Create the app folder in the instance where the application will be. 

```bash
mkdir app 
```

Make a copy of the application and requirements files into the instance 

```bash
scp -i ~/bootcamp-week2-key.pem  ./app/server.py ec2-user@EC2_PUBLIC_IP:~/app/server.py
scp -i ~/bootcamp-week2-key.pem  ./app/requirements.txt ec2-user@EC2_PUBLIC_IP:~/app/requirements.txt
```

The application _server.py_ is deployed in an EC2 instance and has the following features: 
- Production of structured JSON logs. 
- Set correlation IDs for request tracking
- Health check endpoint implementation
- Set log level (ERROR, WARN, INFO)

In order to run the application, first install _pip_ to install the requirements defined in the file _requirements.txt_. 

```bash
sudo dnf install -y python3-pip

pip3 install -r app/requirements.txt
```

### CloudWatch Installation into server 

Install the CloudWatch Agent in the EC2 Instance over SSH

```bash
# Download
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
 
# Install
sudo rpm -U ./amazon-cloudwatch-agent.rpm
 
# Verify installation
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a status -m ec2
```

### Set IAM Role for Server

Create the policies that allow the EC2 Instance to sent the logs and put metric data into CloudWatch: _cloudwatch-logs-policy.json_ and _cloudwatch-metrics-policy.json_. After that, create trust policy _ec2-trust-policy.json_ so EC2 can assume the role. Then, create the IAM role with the trust policy. 

```bash
aws iam create-role \
  --role-name CloudWatchAgentRole \
  --assume-role-policy-document file://ec2-trust-policy.json
```

Create policy using the json definition created before. 

```bash
POLICY_ARN=$(aws iam create-policy \
  --policy-name CloudWatchLogsPolicy \
  --policy-document file://cloudwatch-logs-policy.json \
  --query 'Policy.Arn' \
  --output text)

aws iam put-role-policy \
  --role-name CloudWatchAgentRole \
  --policy-name CloudWatchMetricsPolicy \
  --policy-document file://cloudwatch-metrics-policy.json
``` 

Attach role policy to EC2 instance role

```bash
aws iam attach-role-policy \
  --role-name CloudWatchAgentRole \
  --policy-arn $POLICY_ARN
```

Create instance profile and attach role to the instance

```bash
aws iam create-instance-profile \
  --instance-profile-name CloudWatchAgentProfile
 
aws iam add-role-to-instance-profile \
  --instance-profile-name CloudWatchAgentProfile \
  --role-name CloudWatchAgentRole
 
aws ec2 associate-iam-instance-profile \
  --instance-id i-034a75e71526ec100 \
  --iam-instance-profile Name=CloudWatchAgentProfile
```

### Configure and Run CloudWatch Agent

Save the configuration defined in _cloudwatch-agent-config.json_ into the _config.json_ file on the server by running the following command: 

```bash
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/config.json
```

Start the agent by running the following command: 

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

Run the application: 

```bash 
cd ~/app
nohup python3 server.py > app.log 2>&1 & disown
```

## Custom Metrics Instrumentation 

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

## Monitoring Dashboard

A CloudWatch Dashboard was configured in a hierarchical way as follows: 
- Critical Health Server Information: Request Count, Error Rate, Target Latency and Healthy Targets
- Golden Signals: Request Rate, Error Rate, Latency, Saturation
- Resource Utilization: CPU Usage, Memory Utilization, Network In/Out requests and Disk Space
- Correlation view that compares P95 Latency, Request Rate, HTTP 5XX Code Responses and CPU Usage

The configuration of the dashboard is defined in the file _config/dashboard.json_ and to create/update the dashboard, the following command must be executed: 

```bash
aws cloudwatch put-dashboard \
  --dashboard-name Project2-WebTierMonitoring \
  --dashboard-body file://dashboard.json
```

## Alerting System

### SNS topic configuration

Create an SNS topic, which is the destination that an alarm publishes to. 

```bash
TOPIC_ARN=$(aws sns create-topic \
  --name CloudWatchAlerts \
  --tags Key=Environment,Value=Production \
  --query 'TopicArn' \
  --output text)
```

**Topic ARN:** arn:aws:sns:us-east-1:829910101871:CloudWatchAlerts

After SNS Topic is created, an email is subscribed to receive notifications. 

```bash
aws sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol email \
  --notification-endpoint julioaldana.deu@gmail.com
```

### Alarm 1: CPU Utilization 

The first alarm to be wired to the CloudWatch channel is the CPU Utilization. This metric is published by EC2 itself. For this metric, two alarms were created to warn the engineers before the CPU Usage reaches a critical threshold. 

**Warning Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 2 (10 minutes total)
- Threshold: 70%
- Justification: CPU Usage is high but in a threshold where an action can still be performed.  
- Comparison: GreaterThan

```bash 
aws cloudwatch put-metric-alarm \
  --alarm-name CPU-Warning \
  --alarm-description "Warning: CPU above 70%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 70 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID \
  --alarm-actions $TOPIC_ARN
```

**Critical Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 1
- Threshold: 90%
- Justification: CPU Usage is almost reaching 100%, immediate action must be performed.  
- Comparison: GreaterThan


```bash 
aws cloudwatch put-metric-alarm \
  --alarm-name CPU-Critical \
  --alarm-description "CRITICAL: CPU above 90%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 90 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID \
  --alarm-actions $TOPIC_ARN
```

### Alarm 2: Memory Utilization

The memory utilization is also wired to the CloudWatch channel. This metrics comes from CWAgent, so the metrics collection must be added by creating a filter that will count the matching lines in the log group. 

**Warning Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 2 (10 minutes total)
- Threshold: 70%
- Justification: Memory Usage is high but in a threshold where an action can still be performed.  
- Comparison: GreaterThan

```bash 
aws cloudwatch put-metric-alarm \
  --alarm-name MemoryUsage-Warning \
  --alarm-description "Warning: Memory above 70%" \
  --metric-name mem_used_percent \
  --namespace CWAgent \
  --statistic Average \
  --period 300 \
  --threshold 70 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID \
  --alarm-actions $TOPIC_ARN
```

**Critical Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 1
- Threshold: 90%
- Justification: Memory Usage is almost reaching 100%, immediate action must be performed.  
- Comparison: GreaterThan


```bash 
aws cloudwatch put-metric-alarm \
  --alarm-name MemoryUsage-Critical \
  --alarm-description "Critical: Memory above 90%" \
  --metric-name mem_used_percent \
  --namespace CWAgent \
  --statistic Average \
  --period 300 \
  --threshold 90 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID \
  --alarm-actions $TOPIC_ARN
```

### Alarm 3: Disk Space

**Warning Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 2 (10 minutes total)
- Threshold: 70%
- Justification: Disk Space is running out but in a threshold where an action can still be performed.  
- Comparison: GreaterThan

```bash 
aws cloudwatch put-metric-alarm \
  --alarm-name DiskSpace-Warning \
  --alarm-description "Warning: Disk Space below 30%" \
  --metric-name disk_used_percent \
  --namespace CWAgent \
  --statistic Average \
  --period 300 \
  --threshold 70 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID Name=path,Value=/ Name=device,Value="nvme0n1p1" Name=fstype,Value="xfs" \
  --alarm-actions $TOPIC_ARN
```

**Critical Alarm**

- Period: 300 seconds (5 minutes)
- Evaluation periods: 1
- Threshold: 90%
- Justification: Disk Space is almost full, immediate action must be performed.  
- Comparison: GreaterThan


```bash 
aws cloudwatch put-metric-alarm \
  --alarm-name DiskSpace-Critical \
  --alarm-description "Critical: Disk Space below 10%" \
  --metric-name disk_used_percent \
  --namespace CWAgent \
  --statistic Average \
  --period 300 \
  --threshold 90 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID Name=path,Value=/ Name=device,Value="nvme0n1p1" Name=fstype,Value="xfs" \
  --alarm-actions $TOPIC_ARN
```

### Alarm 4: Application Error Rate Alarm 

Create the alarm with the following parameters: 

- Period: 300 seconds (5 minutes)
- Evaluation periods: 1
- Threshold: 10
- Justification: Having an error rate of 2 errors per minute is sufficient to consider that there is an issue.  
- Comparison: GreaterThan

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name HighErrorRate \
  --alarm-description "Alert when error rate exceeds 10 per 5 minutes" \
  --metric-name ErrorCount \
  --namespace Application \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions $TOPIC_ARN \
  --treat-missing-data notBreaching
```

### Alarm 5: Application Load Balancer Response Time Alert

This alarm is triggered when the Load Balancer response exceeds 500 ms.

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name HighResponseTime \
  --alarm-description "Alert when P95 latency exceeds 500ms" \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --extended-statistic p95 \
  --period 300 \
  --threshold 0.5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=LoadBalancer,Value=$LB_DIMENSION \
  --alarm-actions $TOPIC_ARN
```

## Incident Response Simulation 

### Inject a failure 

The script *app/simulation/saturation_sim.py* sends and increase the number of request from 5 to 50, and simulates error responses on the server. In parallel, the command ```bash stress-ng --cpu 4 --cpu-load 70 --timeout 7m```is used to stress the server to simulate an increase in the CPU utilization.

### Use monitoring to diagnose

**Health Dashboard:** This section of the dashboard shows an increase on the request rate, as well as a high error rate when the request rate increase. 

![Health Dashboard](../evidence/incident-screenshots/01-health-dashboard.png)

**Golden Signals:** This section of the dasboard shows the behavior of the most relevant signals, such as the latency, the error responses and the traffic that has increased.

![Golden Signals](../evidence/incident-screenshots/01-golden-signals.png) 

**EC2 Resource Utilization:** In this section it is possible to see the increasing of the CPU Usage, which is the potential root cause of the problem.

![CPU Usage](../evidence/incident-screenshots/03-cpu-usage.png)

**Correlation View:** With this widget, it is more visible the relationship between the symptoms of the server and the behavior of the resource. The anomalies ocurr simultaneously, and this can be seen really easy with this view.

![Correlation View](../evidence/incident-screenshots/04-correlation-view.png)

### Incident summary

**Incident:** API latency increased from 200ms (P95) to 2,000ms (P95)  
**Impact:** 2,500 users experienced slow page loads, 35% error rate  
**Duration:** 60 minutes (17:00-18:00 UTC, Aug 14, 2024)  
**Root Cause:**  Unexpected traffic/application workload 
**Status:** Resolved

### Possible fixes

**Immediate**

- Stop non-critical batch jobs or scheduled workloads.
- Increase the number of EC2 instances in the ALB
- Restart the application can temporary restore the performance. 
 
**Short-term**

- Implement auto-scaling for ALB
- Optimize the application to find CPU-intensive code.
- Size the instance based on observed CPU Usage
 
**Long-term**

- Perform load tests to determine the maximum sustainable request rate
- Optimize inefficient algorithms, loops, serialization, request processing, or background jobs
