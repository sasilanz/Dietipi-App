# Database Backup & Restore Guide

This guide covers automated database backups and restore procedures for the IT-Kurs application.

## Overview

Your database data is **persistent** and **safe** during normal deployments because:
- Database data is stored in a Docker named volume (`dbdata`)
- Rebuilding/redeploying the application **does not affect** the database
- The database container reuses the same persistent volume

## Automated Backups

### Backup Frequency Recommendations

| Environment | Frequency | Retention |
|-------------|-----------|-----------|
| **Production** | Every 6 hours | 14 days |
| **Staging** | Daily at 2 AM | 7 days |
| **Development** | Weekly | 3 days |

### Setup Automated Backups

**Option 1: Simple interval-based backups (every 6 hours)**
```bash
# For production - runs backup every 6 hours in a loop
docker compose -f compose.yml -f compose.prod.yml -f compose.backup.yml up -d
```

**Option 2: Cron-based backups - Every 6 hours**
```bash
# More precise timing - backups at 00:00, 06:00, 12:00, 18:00
docker compose -f compose.yml -f compose.prod.yml -f compose.backup-cron.yml up -d
```

**Option 3: Daily backups (2 AM)**
```bash
# For staging/smaller apps - one backup per day at 2 AM
docker compose -f compose.yml -f compose.prod.yml -f compose.backup-daily.yml up -d
```

### Configuration

Set these in your `.env` file:
```bash
BACKUP_RETENTION_DAYS=14  # How many days to keep backups
```

## Manual Backup Operations

### Create Manual Backup
```bash
# Run backup script manually
docker compose exec backup /usr/local/bin/backup.sh

# Or run backup container one-time
docker compose run --rm backup
```

### List Available Backups
```bash
# See all backups
docker compose exec backup ls -lh /backups/

# Or access backup volume
docker run --rm -v dieti-it_backup_data:/backups alpine ls -lh /backups/
```

## Restore Operations

### Restore from Latest Backup
```bash
# Copy restore script to backup container and run
docker compose exec backup /usr/local/bin/restore.sh latest
```

### Restore from Specific Backup
```bash
# List available backups first
docker compose exec backup /usr/local/bin/restore.sh

# Restore specific backup
docker compose exec backup /usr/local/bin/restore.sh backup_kursdb_20240901_120000.sql.gz
```

### Emergency Restore from Local File
```bash
# Copy backup to container and restore
docker cp backup.sql.gz $(docker compose ps -q backup):/tmp/
docker compose exec backup /usr/local/bin/restore.sh /tmp/backup.sql.gz
```

## Backup File Management

### Download Backups Locally
```bash
# Copy backup from container to local machine
docker cp $(docker compose ps -q backup):/backups/backup_kursdb_20240901_120000.sql.gz ./
```

### Upload Backup to Container
```bash
# Copy local backup to container
docker cp ./backup.sql.gz $(docker compose ps -q backup):/backups/
```

## Monitoring Backups

### Check Backup Service Status
```bash
# Check if backup service is running
docker compose ps backup

# View backup logs
docker compose logs backup -f
```

### Verify Backup Integrity
```bash
# Test if backup file is valid
docker compose exec backup sh -c "gunzip -t /backups/backup_kursdb_*.sql.gz"
```

## Production Deployment Strategy

### Safe Deployment Process
1. **Before deployment**: Verify recent backups exist
2. **Deploy**: Run your normal deployment
3. **After deployment**: Verify application works
4. **If issues occur**: Use restore procedure

```bash
# Safe production deployment
# 1. Check latest backup
docker compose exec backup ls -lh /backups/ | tail -5

# 2. Deploy (your existing process)
docker compose -f compose.yml -f compose.prod.yml up -d --build

# 3. Verify deployment
curl -f https://your-domain.com/health || echo "Deployment issue detected"
```

## Disaster Recovery

### Complete Environment Recreation
If you need to rebuild everything from scratch:

```bash
# 1. Save current backups (if accessible)
docker cp $(docker compose ps -q backup):/backups ./saved-backups/

# 2. Destroy and recreate
docker compose down -v  # ⚠️ This removes ALL volumes
docker compose -f compose.yml -f compose.prod.yml -f compose.backup.yml up -d

# 3. Restore from backup
docker cp ./saved-backups/latest-backup.sql.gz $(docker compose ps -q backup):/backups/
docker compose exec backup /usr/local/bin/restore.sh latest-backup.sql.gz
```

## Best Practices

### Backup Security
- Backups contain sensitive data - secure the backup storage
- Consider encrypting backup files for extra security
- Regularly test restore procedures

### Monitoring
- Set up alerts for backup failures
- Monitor backup file sizes for anomalies
- Verify backup integrity periodically

### Storage Management
- For high-traffic applications, consider external backup storage (AWS S3, etc.)
- Monitor backup volume disk usage
- Adjust retention based on compliance requirements

## Troubleshooting

### Backup Service Won't Start
```bash
# Check logs
docker compose logs backup

# Check if DB is healthy
docker compose ps db
```

### Backup Files Not Created
```bash
# Check permissions and script
docker compose exec backup ls -la /usr/local/bin/backup.sh
docker compose exec backup cat /var/log/backup.log
```

### Restore Fails
```bash
# Verify backup file integrity
docker compose exec backup gunzip -t /backups/your-backup.sql.gz

# Check database connectivity
docker compose exec backup mysql -h db -u root -p${DB_ROOT_PASSWORD} -e "SHOW DATABASES;"
```

---

**Remember**: Regular deployments are safe! Your data persists automatically. Backups are for disaster recovery and peace of mind. 🚀
