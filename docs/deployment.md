# Deployment 

## Server Setup

### Application with Structured Logging

Launch an EC2 Instance where the application will reside. Access to the EC2 Instance via SSH to install the application. 

```bash
ssh -i ~/bootcamp-week2-key.pem  ec2-user@EC2_PUBLIC_IP
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
nohup python3 server.py > app.log 2>&1 &
disown
```

## Custom Metrics Instrumentation 

At least 5 custom application metrics
Published to CloudWatch
Includes business metrics (not just technical)
Examples: orders/min, cart abandonment, API latency

## Monitoring Dashboard

CloudWatch dashboard with Golden Signals
Request Rate, Error Rate, Latency, Saturation
Resource utilization (CPU, memory, disk)
Visual hierarchy (critical metrics prominent)
Appropriate chart types

## Alerting System 

At least 3 CloudWatch alarms
SNS topic for notifications
Warning and critical thresholds
Email alerts configured
Documented threshold rationale

## Incident Response Simulation 

Inject a failure (high latency, errors, resource exhaustion)
Use monitoring to diagnose
Write incident summary
Document findings with screenshots
Propose fixes