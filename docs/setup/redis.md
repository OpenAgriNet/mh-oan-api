# Redis Stack Production Setup for SVA Application

## Cleanup Existing Installation

```bash
# Stop and remove the container
docker stop redis-stack || true
docker rm redis-stack || true

# Clean up data directory (optional - BE CAREFUL: this deletes all data)
sudo rm -rf /etc/redis/*

# Remove from Docker network (network will be recreated in setup)
docker network rm svanetwork || true
```

## Quick Setup (Copy-Paste Block)

```bash
# Create network and directories
docker network create svanetwork
mkdir -p /etc/redis
chmod 755 /etc/redis

# Create Redis configuration
cat << 'EOF' > /etc/redis/redis.conf
# Memory Configuration
maxmemory 8gb
maxmemory-policy allkeys-lru

# Connection Settings
maxclients 5000
timeout 300
tcp-keepalive 60

# Performance Tuning
appendonly no
save 900 1
save 300 10000
stop-writes-on-bgsave-error no
rdbcompression yes
rdbchecksum yes

# Cache Settings
# Proactively clean cache keys
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
activedefrag yes
active-defrag-ignore-bytes 100mb
active-defrag-threshold-lower 10
active-defrag-threshold-upper 30

# Client Output Buffer Limits
client-output-buffer-limit normal 2gb 1gb 60
client-output-buffer-limit pubsub 512mb 256mb 60

# IOs
io-threads 4
io-threads-do-reads yes

# Logging
loglevel notice
EOF

# Launch Redis Stack
docker run -d \
  --name redis-stack \
  --network svanetwork \
  -p 6379:6379 \
  -p 8001:8001 \
  -v /etc/redis:/data \
  -v /etc/redis/redis.conf:/redis-stack.conf \
  --restart always \
  redis/redis-stack:latest

# Verify Configuration
sleep 5  # Wait for container to start
docker exec -it redis-stack redis-cli INFO memory | grep used_memory_human
docker exec -it redis-stack redis-cli CONFIG GET maxmemory
docker exec -it redis-stack redis-cli CONFIG GET maxmemory-policy
```

## System Requirements
- 16GB RAM server
- 8 CPU cores
- 200GB storage
- Docker installed and running

## Configuration Details

### Memory Management
- Total allocation: 8GB
- Eviction Policy: `allkeys-lru`
  - Uses Least Recently Used (LRU) algorithm
  - Applies to all keys (not just keys with TTL)
  - Better for mixed-use cases (cache + storage)
  - Reasons for choosing `allkeys-lru`:
    1. Django cache TTL set to 7 days (reduced from 60)
    2. Message history might not have TTLs
    3. Suggestions data might not have TTLs
    4. More predictable memory management

### Cache Optimization
- Lazy freeing: Prevents blocking during eviction
- Active defragmentation: Optimizes memory usage
- Defrag thresholds: 10-30% fragmentation triggers optimization
- Minimum defrag size: 100MB (prevents unnecessary defrag)

### Memory Allocation (8GB for Redis)
- Gunicorn (17 workers × 4 threads ≈ 2-3GB)
- Celery workers (10 workers ≈ 1-2GB)
- OS and system processes (2-3GB)
- Safety margin for memory spikes

### Connection Settings
- 5000 max clients:
  - Django connection pool (1000 connections)
  - Celery workers (170 connections)
  - Additional margin for services and monitoring
- 300s timeout for idle connections
- 60s TCP keepalive

### Data Persistence
- Snapshots:
  - Every 15 minutes if ≥1 key changed
  - Every 5 minutes if ≥10000 keys changed
- Compression enabled
- Continues writes during background save errors

### Performance
- 4 I/O threads (half of CPU cores)
- Output buffer limits:
  - Normal: 2GB hard / 1GB soft
  - Pub/Sub: 512MB hard / 256MB soft

## Monitoring Commands

```bash
# Memory usage
docker exec -it redis-stack redis-cli INFO memory

# Client connections
docker exec -it redis-stack redis-cli INFO clients

# Command statistics
docker exec -it redis-stack redis-cli INFO commandstats

# Backup
docker exec -it redis-stack redis-cli SAVE
docker cp redis-stack:/data/dump.rdb /backup/redis/dump.rdb
```

## Maintenance Guidelines

### Memory Usage >80%
1. Review key expiration policies
2. Monitor memory usage patterns
3. Consider Redis Cluster setup

### High CPU Usage
1. Check SLOWLOG: `docker exec -it redis-stack redis-cli SLOWLOG GET`
2. Review query patterns
3. Monitor command statistics

## Container Management
- Container auto-restarts on failure
- Auto-starts on system boot
- Use `docker stop redis-stack` to stop
- Use `docker logs redis-stack` to check logs