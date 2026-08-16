# Troubleshooting guide 

## Common Issues

### High CPU Utilization

- [ ] Identify the affected EC2 instance/service.
- [ ] Check CPU utilization in CloudWatch and determine how long it has been elevated.
- [ ] Check whether traffic/request volume has increased.
- [ ] Identify processes consuming excessive CPU.
- [ ] If caused by expected traffic, scale the service/instance if necessary.
- [ ] If caused by a runaway process, restart the affected service if safe.
- [ ] Monitor CPU until it returns to normal.
- [ ] Escalate if CPU remains high or the application is unavailable.

### High Memory Utilization

- [ ] Identify the affected EC2 instance/container.
- [ ] Check memory utilization and available memory.
- [ ] Identify processes consuming the most memory.
- [ ] Check for recent deployments or configuration changes.
- [ ] If memory usage is caused by a temporary issue, restart the affected service if appropriate.
- [ ] If the workload legitimately requires more memory, scale the instance/container.
- [ ] Monitor memory usage after remediation.
- [ ] Escalate if memory continues to increase or the application becomes unstable.

### Low Disk Space

- [ ] Identify the affected instance and filesystem.
- [ ] Check disk usage and identify which directories/files are consuming space.
- [ ] Check application and system logs.
- [ ] Check whether log rotation is working correctly.
- [ ] Safely remove unnecessary temporary files or old logs according to the retention policy.
- [ ] If appropriate, archive data to durable storage such as S3.
- [ ] If additional capacity is required, increase the EBS volume.
- [ ] Verify sufficient free space is available.
- [ ] Confirm the CloudWatch alarm returns to OK.
- [ ] Escalate if disk space continues to decrease or cannot safely be freed.

### High Application Error Rate

- [ ] Check the error-rate CloudWatch metric and determine when the problem started.
- [ ] Check application logs for the specific errors.
- [ ] Check whether there was a recent deployment or configuration change.
- [ ] Check dependent services such as databases, APIs, queues, and other AWS services.
- [ ] Determine whether the problem affects all users or a specific endpoint.
- [ ] If a recent deployment caused the issue, consider rolling it back.
- [ ] If the service is overloaded, scale it if appropriate.
- [ ] Monitor the error rate after taking corrective action.
- [ ] Escalate immediately if the application remains unavailable or customer impact is significant.

### High Response Time

- [ ] Identify the affected application/service or endpoint.
- [ ] Check when the latency increase started.
- [ ] Check request volume and traffic patterns.
- [ ] Compare latency with CPU, memory, disk, and network metrics.
- [ ] Check application logs and traces for slow operations.
- [ ] Check database performance and slow queries.
- [ ] Check external API/dependency latency.
- [ ] Check for recent deployments or configuration changes.
- [ ] Scale the affected service if the problem is capacity-related.
- [ ] Roll back a recent change if it is identified as the likely cause.
- [ ] Monitor response time until it returns to the normal range.
- [ ] Escalate if latency remains high or customers are experiencing significant impact.

## Useful commands for troubleshooting and verification 

### Generate requests

ALB DNS: logging-p2-alb-1152847628.us-east-1.elb.amazonaws.com

-  General request 

```bash
curl http://$ALB_DNS/
```

- Health check endpoint 

```bash
curl http://$ALB_DNS/health
```

- Order request 

```bash
curl -X POST http://$ALB_DNS/order \
  -H "Content-Type: application/json" \
  -d '{"amount": 99.99, "items": 3, "user_id": "user-123"}'
```

- Generate multiple requests

```bash
for i in {1..50}; do
  curl http://$ALB_DNS/ &
done
```

- Simulate requests

Refer to *app/simulation/saturation_sim.py*


### Simulate high CPU Usage 

```bash
# Install stress-ng
sudo dnf install -y stress-ng

# Trigger the 70% warning alarm, but stay below 90%
stress-ng --cpu 4 --cpu-load 75 --timeout 5m

# Push CPU above 90%
stress-ng --cpu 4 --cpu-load 95 --timeout 5m
```


### CloudWatch logs and streams verification

- List log groups

```bash
aws logs describe-log-groups
```

-List log streams

```bash
aws logs describe-log-streams --log-group-name /aws/application/api
```

- Tail logs

```bash
aws logs tail /aws/application/api --follow
```

- Get recent events

```bash
aws logs get-log-events \
  --log-group-name /aws/application/api \
  --log-stream-name i-your-instance-id \
  --limit 10
  ```

## Test SNS Topic 

```bash
aws sns publish \
  --topic-arn $TOPIC_ARN \
  --subject "Test Alert" \
  --message "This is a test alert from CloudWatch"
```
