# Alerting System 

## Alert strategy

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

## Alarm 5: Application Load Balancer Response Time Alert

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


## SNS topic configuration

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

## Response procedures

## Runbook for each alert