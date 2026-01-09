# Credential Rotation Quick Reference
## Fast Action Guide

**Time to Complete:** ~15 minutes per credential
**Priority:** CRITICAL - Execute immediately

---

## 🚨 Slack Webhook Rotation (5 minutes)

### Step 1: Generate New Webhook (2 min)
```
1. Go to: https://api.slack.com/apps
2. Select app → Features → Incoming Webhooks
3. Click: "Add New Webhook to Workspace"
4. Select channel → Allow
5. Copy new webhook URL
```

### Step 2: Test New Webhook (1 min)
```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test from rotation"}' \
  https://hooks.slack.com/services/YOUR/NEW/WEBHOOK
```

### Step 3: Update Production (2 min)
```bash
ssh ec2-user@18.118.142.110
cd birthdays-to-slack/
nano .env  # Update WEBHOOK_URL
docker compose down && docker compose up -d
```

### Step 4: Revoke Old Webhook (1 min)
```
1. Return to https://api.slack.com/apps
2. Find old webhook → Remove
```

---

## 🔑 OpenAI API Key Rotation (5 minutes)

### Step 1: Generate New Key (2 min)
```
1. Go to: https://platform.openai.com/api-keys
2. Click: "+ Create new secret key"
3. Name: "birthdays-to-slack-production-2025-11"
4. Copy key immediately (can't view again!)
```

### Step 2: Test New Key (1 min)
```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-proj-YOUR-NEW-KEY" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```

### Step 3: Update Production (2 min)
```bash
ssh ec2-user@18.118.142.110
cd birthdays-to-slack/
nano .env  # Update OPENAI_API_KEY
docker compose down && docker compose up -d
```

### Step 4: Revoke Old Key (1 min)
```
1. Return to https://platform.openai.com/api-keys
2. Find old key → ... → Revoke
```

---

## ✅ Verification Checklist

After rotation, verify everything works:

- [ ] Health check passes: `curl http://localhost:5002/health`
- [ ] Dashboard loads: http://18.118.142.110:5002
- [ ] Click "Regenerate Message" on any birthday
- [ ] Verify message appears
- [ ] Check logs: `docker compose logs -f`
- [ ] No error messages
- [ ] Test message sent to Slack (if enabled)

---

## 🔄 Update Local Environment

Don't forget your local dev environment:

```bash
cd ~/git/birthdays-to-slack
nano .env  # Update both credentials
docker compose -f docker-compose.dev.yml up --build
```

---

## 📊 Monitoring (First Week)

Daily checks:
```bash
# Check application logs
docker compose logs --tail=100 birthdays-to-slack

# Check OpenAI usage
# Visit: https://platform.openai.com/usage

# Check health endpoint
curl http://18.118.142.110:5002/health
```

---

## 🆘 Emergency Rollback

If something breaks:
```bash
ssh ec2-user@18.118.142.110
cd birthdays-to-slack/
cp .env.backup.YYYYMMDD .env
docker compose down && docker compose up -d
```

---

## 📅 Set Reminder

**Next Rotation Due:** 90 days from today (February 8, 2026)

Add to calendar:
- Title: "Rotate birthdays-to-slack credentials"
- Date: 2026-02-08
- Description: "Follow rotation quick reference guide"

---

## 📚 Full Documentation

For detailed procedures, see: `/docs/CREDENTIAL_ROTATION_PLAN.md`
