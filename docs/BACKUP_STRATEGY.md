# Backup Strategy for Configuration Files

This document outlines the backup strategy for `.env` files and application data in the Birthdays to Slack application.

## Manual .env Backup

Create a manual backup of your configuration files:

```bash
# Create backup directory with timestamp
BACKUP_DIR="backups/env-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup all .env files
cp .env "$BACKUP_DIR/.env" 2>/dev/null || echo "No .env file found"
cp deploy/.env "$BACKUP_DIR/deploy.env" 2>/dev/null || echo "No deploy/.env file found"
cp .env.example "$BACKUP_DIR/.env.example" 2>/dev/null || echo "No .env.example file found"

# Create checksums for verification
cd "$BACKUP_DIR"
sha256sum * > checksums.txt
cd -

echo "Backup created in: $BACKUP_DIR"
```

**Important**: Never commit `.env` files to git. The `backups/` directory should also not be committed to prevent credentials from being exposed in version control.

## Backup Locations

### Local Encrypted Backups (Recommended)

**Create encrypted backup:**
```bash
# Create backup
BACKUP_DIR="backups/env-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp .env "$BACKUP_DIR/.env" 2>/dev/null || true
cp deploy/.env "$BACKUP_DIR/deploy.env" 2>/dev/null || true

# Encrypt with GPG
cd backups
tar -czf - "env-$(date +%Y%m%d-%H%M%S)" | \
  gpg --symmetric --cipher-algo AES256 --output "env-backup-$(date +%Y%m%d-%H%M%S).tar.gz.gpg"

# Remove unencrypted backup
rm -rf "env-$(date +%Y%m%d-%H%M%S)"
cd -

echo "Encrypted backup created"
```

**Restore from encrypted backup:**
```bash
# List available backups
ls -lh backups/*.gpg

# Decrypt and extract
gpg --decrypt backups/env-backup-YYYYMMDD-HHMMSS.tar.gz.gpg | tar -xzf -

echo "Backup restored to: env-YYYYMMDD-HHMMSS/"
```

### Secure Storage Recommendations

Keep encrypted `.env` backups in one of these locations:

1. **Local encrypted storage**: Encrypted external hard drive or USB drive (keep offline)
2. **Cloud encrypted storage**: Services like Tresorit, Sync.com, or encrypted cloud storage with client-side encryption
3. **Password manager**: Secure password managers with document storage capabilities
4. **Never store unencrypted backups in**: Public cloud storage, email, messaging apps, or version control

## Disaster Recovery Procedures

### Lost or Corrupted .env Files

If your `.env` files are lost or corrupted:

```bash
# 1. Stop running services
docker compose down

# 2. Restore .env files from encrypted backup
gpg --decrypt backups/env-backup-LATEST.tar.gz.gpg | tar -xzf -

# 3. Copy to working directory
cp env-YYYYMMDD-HHMMSS/.env .env
cp env-YYYYMMDD-HHMMSS/deploy.env deploy/.env 2>/dev/null || true

# 4. Verify files are restored correctly
ls -la .env deploy/.env 2>/dev/null

# 5. Start services
docker compose up -d

# 6. Verify health
curl http://localhost:5002/health
```

## Verify Backup Integrity

After creating backups, verify they can be successfully restored:

```bash
# List available backups
ls -lh backups/

# Test decryption of backup
gpg --decrypt backups/env-backup-YYYYMMDD-HHMMSS.tar.gz.gpg > /dev/null

if [ $? -eq 0 ]; then
    echo "✓ Backup can be decrypted successfully"
else
    echo "✗ Backup decryption failed"
fi

# Verify checksums from backup
cd backups/env-YYYYMMDD-HHMMSS
sha256sum --check checksums.txt
cd -
```

## Backup Retention Policy

### Development Environments
- **Encrypted backups**: Keep for 90 days
- **Automated cleanup**: Delete encrypted backups older than 90 days

### Production Environments
- **Weekly encrypted backups**: Keep for 90 days
- **Monthly encrypted backups**: Keep for 1 year
- **Critical backups**: Keep indefinitely (store in separate secure location)

### Automated Cleanup

```bash
# Add to crontab for weekly cleanup
# 0 2 * * 0 /path/to/cleanup-backups.sh

cat > cleanup-backups.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/Users/brent/git/birthdays-to-slack/backups"

# Delete unencrypted backups older than 7 days
find "$BACKUP_DIR" -name "env-*" -type d -mtime +7 -exec rm -rf {} +

# Delete encrypted backups older than 90 days
find "$BACKUP_DIR" -name "*.gpg" -type f -mtime +90 -delete

echo "Backup cleanup complete"
EOF

chmod +x cleanup-backups.sh
```

## Docker Volume Backups

Backup application data stored in Docker volumes:

```bash
# List volumes
docker volume ls

# Backup a specific volume
docker run --rm -v birthdays-to-slack_app-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/app-data-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .

# Restore from volume backup
docker run --rm -v birthdays-to-slack_app-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/app-data-YYYYMMDD-HHMMSS.tar.gz -C /data
```

Store volume backups with the same encryption and retention policies as `.env` backups.

## Testing Backup/Restore

### Monthly Drill

Run this test monthly to ensure backups are working:

```bash
#!/bin/bash
# Monthly backup/restore test

echo "=== Backup/Restore Test ==="

# 1. Create test backup
TEST_DIR="backups/test-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$TEST_DIR"
cp .env "$TEST_DIR/.env" 2>/dev/null || echo "No .env to backup"

# 2. Test encryption
tar -czf - "$TEST_DIR" | \
  gpg --symmetric --cipher-algo AES256 --batch --passphrase "test123" \
  --output "$TEST_DIR.tar.gz.gpg"

# 3. Test decryption
gpg --decrypt --batch --passphrase "test123" "$TEST_DIR.tar.gz.gpg" | \
  tar -xzf - -O > /dev/null

if [ $? -eq 0 ]; then
    echo "✓ Backup/restore test passed"
else
    echo "✗ Backup/restore test failed"
    exit 1
fi

# 4. Cleanup
rm -rf "$TEST_DIR" "$TEST_DIR.tar.gz.gpg"

echo "Test complete"
```

## Disaster Recovery Checklist

- [ ] Locate most recent encrypted backup
- [ ] Verify backup integrity (checksums)
- [ ] Stop running services
- [ ] Decrypt and restore .env files from backup
- [ ] Verify restored .env contains all required variables
- [ ] Start services with restored configuration
- [ ] Verify application health (check /health endpoint)
- [ ] Check logs for errors
- [ ] Verify Slack and OpenAI connectivity
- [ ] Document what went wrong and why
- [ ] Update backup procedures if needed

## Security Best Practices

### 1. Backup Encryption Keys

Protect your GPG encryption keys:

```bash
# Export GPG key for backup encryption
gpg --export-secret-keys your-key-id > gpg-backup-key.asc

# Store GPG key separately from backups
# Keep in a secure location (encrypted external drive, password manager, etc.)
```

**Important**: Keep GPG keys separate from encrypted backups. If someone obtains both, they can decrypt your backups.

### 2. Multiple Backup Locations

Store backups in multiple secure locations:

- Local encrypted backups (development machine)
- Offline encrypted storage (USB drive, external hard drive)
- Secure cloud storage with client-side encryption (Tresorit, Sync.com)
- Do NOT store backups in email, messaging apps, or public cloud storage

### 3. Access Documentation

Maintain a secure document with:

- Location of encrypted backups
- Location of GPG key backup
- GPG encryption passphrase (stored securely, not with backups)
- Recovery procedures
- Emergency contact information

Store this documentation in a secure location accessible only to authorized personnel.

### 4. Regular Testing

Restore from backups regularly to verify they work:

- Test monthly backup restoration
- Test GPG decryption procedure
- Document any issues and update procedures
- Keep a log of successful restore tests

## Application Data Backups

Keep regular backups of application data:

- **history.json**: Birthday message history (prevents duplicates)
- **Docker volumes**: Persistent application data
- **Database backups**: If using external databases

### Backup Schedule

```bash
# Daily backup of critical files
0 2 * * * /path/to/backup-app-data.sh

# Weekly encrypted backup
0 3 * * 0 /path/to/backup-encrypted.sh

# Monthly verification
0 4 1 * * /path/to/verify-backups.sh
```

## Regular Maintenance

### Weekly
- Check backup disk space
- Verify encrypted backups exist
- Confirm application health

### Monthly
- Run backup/restore drill
- Test GPG decryption
- Clean up old backups (older than retention policy)
- Verify backup integrity with checksums
- Test Docker volume restoration

### Quarterly
- Review and update backup strategy
- Test full disaster recovery procedure
- Update documentation
- Audit access logs to backup storage
