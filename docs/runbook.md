# Troubleshooting guide 

## Generate requests

-  General request 

```bash
curl http://localhost:5000/
```

- Health check endpoint 

```bash
curl http://localhost:5000/health
```

- Order request 

```bash
curl -X POST http://localhost:5000/order \
  -H "Content-Type: application/json" \
  -d '{"amount": 99.99, "items": 3, "user_id": "user-123"}'
```

- Generate multiple requests

```bash
for i in {1..50}; do
  curl http://localhost:5000/ &
done
```

## CloudWatch logs and streams verification

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