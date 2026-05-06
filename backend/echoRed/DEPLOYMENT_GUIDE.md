# VidyutSeva Deployment & Setup Guide

## Prerequisites

- Python 3.10+
- AWS account with Bedrock access
- PostgreSQL 13+ (for production RDS)
- Docker (optional, for containerization)
- npm/nodejs (for CDK deployment)

---

## Local Development Setup

### 1. Install Dependencies

```bash
cd /workspaces/Eliyonix/backend/echoRed

# Install Python dependencies
pip install -e .

# Or use uv (faster)
uv pip install -e .
```

### 2. Configure AWS Credentials

```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1

# Or use AWS CLI
aws configure
```

### 3. Set Environment Variables

```bash
# Development
export LOCAL_DEV=1
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Optional: RDS for persistent storage
export RDS_CONNECTION_STRING=postgresql://user:pass@localhost:5432/vidyutseva
```

### 4. Run Local Development Server

```bash
# Start Bedrock AgentCore dev server
agentcore dev

# In another terminal, test the agent
agentcore invoke --dev '{"sensor_data": {"voltage": 415.0, "current": 8.0, "temperature": 32.0, "timestamp": 1234567890, "inverter_id": "INV_001", "village_id": "KA_001"}}'
```

---

## Testing

### Run Integration Tests

```bash
pytest test/test_vidyutseva.py -v

# With coverage
pytest test/test_vidyutseva.py --cov=src --cov-report=html
```

### Manual Testing

```bash
# Test with normal sensor data
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_data": {
      "voltage": 415.0,
      "current": 8.0,
      "temperature": 32.0,
      "timestamp": 1234567890,
      "inverter_id": "INV_001",
      "village_id": "KA_001"
    }
  }'

# Test with fault conditions
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_data": {
      "voltage": 430.0,
      "current": 8.0,
      "temperature": 45.0,
      "timestamp": 1234567890,
      "inverter_id": "INV_001",
      "village_id": "KA_001"
    }
  }'
```

---

## Docker Deployment

### Build Docker Image

```bash
# From echoRed directory
docker build -t vidyutseva:latest .

# Verify
docker images | grep vidyutseva
```

### Run Docker Container

```bash
# With AWS credentials
docker run -d \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -p 8000:8000 \
  -p 8080:8080 \
  -p 9000:9000 \
  --name vidyutseva-dev \
  vidyutseva:latest

# Verify container is running
docker logs vidyutseva-dev

# Test
curl http://localhost:8000/invocations -X POST -H "Content-Type: application/json" -d '...'
```

### Docker Compose (Optional)

```yaml
version: '3.8'

services:
  vidyutseva:
    build: .
    ports:
      - "8000:8000"
      - "8080:8080"
      - "9000:9000"
    environment:
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      AWS_DEFAULT_REGION: us-east-1
      RDS_CONNECTION_STRING: postgresql://user:pass@postgres:5432/vidyutseva
    depends_on:
      - postgres
    networks:
      - vidyutseva-net

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: vidyutseva
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: vidyutseva
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - vidyutseva-net

networks:
  vidyutseva-net:
    driver: bridge

volumes:
  postgres_data:
```

Run with:
```bash
docker-compose up -d
```

---

## AWS CDK Deployment

### 1. Bootstrap AWS Environment (First Time Only)

```bash
cd cdk
npm install

# Bootstrap CDK
npm run cdk bootstrap
```

### 2. Synthesize CloudFormation

```bash
npm run cdk synth
```

### 3. Deploy to AWS

```bash
npm run cdk:deploy

# Or manual CDK deploy
cdk deploy
```

### 4. Monitor Deployment

```bash
# Get CloudFormation stack status
aws cloudformation describe-stacks --stack-name vidyutseva-stack

# View logs
aws logs tail /aws/lambda/vidyutseva-agent --follow
```

---

## Production Setup

### 1. Set Up RDS PostgreSQL

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier vidyutseva-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username vidyutseva \
  --master-user-password <secure_password> \
  --allocated-storage 20

# Wait for instance to be available
aws rds describe-db-instances --db-instance-identifier vidyutseva-db

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier vidyutseva-db \
  --query 'DBInstances[0].Endpoint.Address'
```

### 2. Initialize Database

```bash
# Connect to RDS
psql -h <rds-endpoint> -U vidyutseva -d vidyutseva

# Create tables
CREATE TABLE agent_memory (
    agent_name VARCHAR(255) PRIMARY KEY,
    memory_json JSONB NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_messages (
    message_id VARCHAR(36) PRIMARY KEY,
    from_agent VARCHAR(255),
    to_agent VARCHAR(255),
    message_type VARCHAR(50),
    payload JSONB,
    timestamp BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_outcomes (
    alert_id VARCHAR(36) PRIMARY KEY,
    fault_type VARCHAR(100),
    predicted_fault BOOLEAN,
    actual_fault BOOLEAN,
    was_useful BOOLEAN,
    technician_response_time INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_memory_updated ON agent_memory(last_updated);
CREATE INDEX idx_agent_messages_timestamp ON agent_messages(timestamp);
```

### 3. Configure Environment for Production

```bash
# Set production environment variables
export ENVIRONMENT=production
export RDS_CONNECTION_STRING=postgresql://user:pass@vidyutseva-db.xxxxx.us-east-1.rds.amazonaws.com:5432/vidyutseva
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
export LOG_LEVEL=INFO
export TWILIO_ACCOUNT_SID=<your_account_sid>
export TWILIO_AUTH_TOKEN=<your_auth_token>
export TWILIO_WHATSAPP_NUMBER=+1234567890
```

### 4. Deploy to AWS Lambda

```bash
cd cdk

# Update cdk.json with production settings
# Deploy
npm run cdk:deploy -- --require-approval never

# Get API endpoint
aws apigateway get-rest-apis --query 'items[?name==`vidyutseva-api`].id' --output text

# Get CloudWatch logs
aws logs tail /aws/lambda/vidyutseva-agent --follow
```

---

## Monitoring & Logging

### CloudWatch Logs

```bash
# View real-time logs
aws logs tail /aws/lambda/vidyutseva-agent --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/vidyutseva-agent \
  --filter-pattern "ERROR"

# Get statistics
aws logs describe-metric-filters \
  --log-group-name /aws/lambda/vidyutseva-agent
```

### X-Ray Tracing

```bash
# Enable X-Ray
aws lambda update-function-configuration \
  --function-name vidyutseva-agent \
  --tracing-config Mode=Active

# View traces
aws xray get-trace-summaries --start-time 2024-01-01T00:00:00Z
```

### Metrics (CloudWatch)

```bash
# Agent execution latency
aws cloudwatch get-metric-statistics \
  --namespace VidyutSeva \
  --metric-name AgentLatency \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average,Maximum
```

---

## Troubleshooting

### Common Issues

#### 1. Bedrock Model Not Available

**Error**: `Model not found in region`

**Solution**:
```bash
# Check available models in your region
aws bedrock list-foundation-models --region us-east-1

# Change model ID in environment
export BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

#### 2. RDS Connection Timeout

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check RDS security group
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Add inbound rule for your IP
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 5432 \
  --cidr your.ip.address/32
```

#### 3. Out of Memory Errors

**Error**: `MemoryError in Isolation Forest`

**Solution**:
```python
# Reduce contamination parameter in fault_detector.py
self.isolation_forest = IsolationForest(
    contamination=0.05,  # Reduced from 0.1
    n_estimators=50,     # Reduced from 100
)
```

#### 4. High Latency

**Cause**: Bedrock calls taking 2+ seconds

**Solution**:
- Use Bedrock caching for prompts
- Implement circuit breaker for Bedrock calls
- Use fallback alerts instead of always calling Bedrock

---

## Performance Tuning

### Optimize Agent Latency

```python
# In agents/fault_detector.py
# Reduce Isolation Forest features
contamination=0.1,       # Adjust based on fault rate
n_estimators=50,         # Fewer trees = faster, less accurate
random_state=42
```

### Optimize Memory Store

```python
# Use Redis instead of in-memory for scalability
from redis import Redis

class RedisMemoryStore(MemoryStore):
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)
    
    async def save_agent_memory(self, agent_name: str, memory: Dict):
        await self.redis.set(f"agent:{agent_name}", json.dumps(memory))
```

### Optimize A2A Protocol

```python
# Increase timeout for high-latency networks
broker = A2AMessageBroker(timeout_seconds=10)

# Use batch messaging for multiple queries
```

---

## Backup & Recovery

### Backup RDS

```bash
# Create snapshot
aws rds create-db-snapshot \
  --db-instance-identifier vidyutseva-db \
  --db-snapshot-identifier vidyutseva-backup-$(date +%Y%m%d)

# List snapshots
aws rds describe-db-snapshots --db-instance-identifier vidyutseva-db
```

### Restore from Snapshot

```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier vidyutseva-db-restored \
  --db-snapshot-identifier vidyutseva-backup-20240101
```

---

## Security Best Practices

1. **Use AWS Secrets Manager** for credentials
```bash
aws secretsmanager create-secret \
  --name vidyutseva/rds \
  --secret-string '{"username":"vidyutseva","password":"xxxxx"}'
```

2. **Enable RDS encryption**
```bash
aws rds modify-db-instance \
  --db-instance-identifier vidyutseva-db \
  --storage-encrypted \
  --apply-immediately
```

3. **Use VPC for Lambda & RDS**
```bash
# Deploy Lambda in same VPC as RDS
aws lambda update-function-configuration \
  --function-name vidyutseva-agent \
  --vpc-config SubnetIds=subnet-xxxxx SecurityGroupIds=sg-xxxxx
```

4. **Enable audit logging**
```bash
# RDS audit logging
aws rds modify-db-instance \
  --db-instance-identifier vidyutseva-db \
  --enable-cloudwatch-logs-exports postgresql
```

---

## Scale-Out Architecture

For handling 10K+ sensors:

1. **Message Queue**: Upgrade from in-memory to AWS SQS
2. **Distributed Cache**: Use ElastiCache (Redis)
3. **Multi-Lambda**: Deploy multiple Lambda functions for parallel processing
4. **RDS Replica**: Add read replicas for scaling reads

---

## References

- AWS Bedrock: https://aws.amazon.com/bedrock/
- AWS CDK: https://aws.amazon.com/cdk/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- LangGraph: https://github.com/langchain-ai/langgraph

---

**Need Help?** Check CloudWatch logs or reach out to the team.
