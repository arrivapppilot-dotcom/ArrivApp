# Automated Daily Test Faker

Automated system that runs daily at 8 AM UTC to test all scenarios across all schools, generate realistic test data, and validate report generation.

## Features

✅ **Daily Test Cycle**
- Creates 10 new test students per school daily
- Simulates realistic check-ins, late arrivals, and absences
- Generates justifications for absent students
- Appends data daily (builds historical dataset)

✅ **Comprehensive Report Testing**
- Validates students data exists and is queryable
- Validates check-ins data exists and calculations work
- Validates justifications data exists
- Validates late arrivals can be calculated
- Validates absence justifications can be calculated
- Tests historical analytics calculations

✅ **Data Archival**
- Archives daily test data with timestamp
- Stores in `backend/test_data_archive/` folder
- JSON format for historical analysis
- 30-day retention on GitHub Actions

✅ **Email Reporting**
- Sends daily test report to admin email
- Includes test summary and results
- Shows any errors or warnings
- HTML formatted for easy reading

## Setup

### 1. Required Environment Variables

Add these to your Render environment variables or GitHub Actions secrets:

```bash
# Database (already configured)
DATABASE_URL=postgresql://user:password@host/dbname

# Email Configuration (for test reports)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@yourschool.com
```

### 2. Configure Gmail (Recommended)

If using Gmail:

1. Enable 2-Factor Authentication on your Gmail account
2. Create an App Password: https://myaccount.google.com/apppasswords
3. Use the generated 16-character password as `SMTP_PASSWORD`

### 3. Add to Render Environment

1. Go to Dashboard → arrivapp-backend service
2. Settings → Environment
3. Add the variables:
   - `SMTP_SERVER=smtp.gmail.com`
   - `SMTP_PORT=587`
   - `SMTP_USERNAME=<your-gmail>`
   - `SMTP_PASSWORD=<app-password>`
   - `ADMIN_EMAIL=<admin-email>`

### 4. Verify GitHub Actions Secrets

1. Go to Repository Settings → Secrets and variables → Actions
2. Verify these secrets exist:
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_NAME`
   - `SMTP_SERVER`
   - `SMTP_PORT`
   - `SMTP_USERNAME`
   - `SMTP_PASSWORD`
   - `ADMIN_EMAIL`

## Usage

### Automatic (8 AM UTC Daily)

The workflow runs automatically via GitHub Actions schedule:
- **Time**: 8 AM UTC (3 AM EST, 12 AM PST)
- **Frequency**: Daily
- **Triggered by**: `.github/workflows/daily_faker.yml`

### Manual Trigger

Run anytime via GitHub Actions:

1. Go to GitHub → ArrivApp repo
2. Actions tab
3. Select "Daily Automated Test Faker" workflow
4. Click "Run workflow" → "Run workflow"
5. Wait 5-10 minutes for completion

### Local Testing

Run locally before deployment:

```bash
cd /Users/lucaalice/Desktop/AI\ projects/ArrivApp/backend

# Make sure your local database is running and DATABASE_URL is set
python populate_daily.py
```

## Test Data Archive

### Location
```
backend/test_data_archive/
├── test_data_20251117_080000.json
├── test_data_20251116_080000.json
└── test_data_20251115_080000.json
```

### Archive Format
```json
{
  "timestamp": "2025-11-17T08:00:00.123456",
  "test_data_summary": {
    "students_created": 50,
    "checkins_today": 420,
    "justifications_today": 15,
    "late_arrivals": 85,
    "emails_sent": 68
  },
  "schools_tested": 5,
  "test_results": {
    "students_exist": true,
    "checkins_exist": true,
    "justifications_exist": true,
    "today_checkins_calculable": true,
    "late_arrivals_calculable": true,
    "absence_justifications_calculable": true
  },
  "errors": [],
  "warnings": []
}
```

### Download Historical Data

From GitHub Actions:
1. Go to Actions tab
2. Click "Daily Automated Test Faker" workflow
3. Find your run
4. Click "Artifacts"
5. Download `test_data_archive_<run_number>.zip`

## Daily Test Scenarios

### Students Created
- **Per School**: 10 new test students
- **Naming**: `Test{YYYYMMDD}{SchoolID}{Random}`
- **Email**: `firstname.lastname.daily{YYYYMMDD}@example.com`
- **Classes**: Randomly assigned to 1A-6C

### Check-ins Simulated
- **Attendance Rate**: 85%
- **Late Rate**: 20% of attendees
- **Early Checkout**: 5% of attendees
- **Late Time**: 8:15 AM - 9:30 AM
- **On-time**: 7:00 AM - 8:10 AM
- **Checkout**: 2:00 PM - 4:00 PM

### Justifications
- **Absent Rate**: 15% of students
- **Justified**: 40% of absences
- **Types**: Illness, Medical appointment, Family emergency, Personal matter
- **Status**: Mix of pending, approved, rejected

### Data Appended
- **Days Tested**: Today + Yesterday
- **Historical**: All previous days remain
- **Retention**: 30 days on GitHub, permanent in database

## Reports Tested

The automated faker validates all 6 report endpoints:

1. **Statistics** (`/api/reports/statistics`)
   - Total students, present, late, justified, etc.
   - Per school and system-wide

2. **Attendance History** (`/api/reports/attendance-history`)
   - Check-in records with dates
   - Filters by date range

3. **Tardiness Analysis** (`/api/reports/tardiness-analysis`)
   - Late arrival patterns
   - Trends and statistics

4. **Historical Analytics** (`/api/reports/historical-analytics`)
   - Long-term data analysis
   - Patterns across weeks/months

5. **Export PDF** (`/api/reports/export-pdf`)
   - Report generation in PDF format
   - File serving validation

6. **Database Integrity**
   - Students can be queried
   - Check-ins can be aggregated
   - Justifications can be calculated

## Email Report Example

```
✅ ArrivApp Daily Test Report - 2025-11-17 [PASSED]

Date: 2025-11-17 08:00:00 UTC
Status: PASSED

Test Summary
- Schools Tested: 5
- Students Created: 50
- Check-ins Simulated: 420
- Justifications Created: 15

Report Tests
✅ students_exist: PASS
✅ checkins_exist: PASS
✅ justifications_exist: PASS
✅ today_checkins_calculable: PASS
✅ late_arrivals_calculable: PASS
✅ absence_justifications_calculable: PASS
```

## Troubleshooting

### Email Not Sending

**Problem**: Email report doesn't arrive

**Solutions**:
1. Verify email credentials in Render environment
2. Check Gmail app password is correct (16 characters)
3. Check Gmail 2FA is enabled
4. Check ADMIN_EMAIL is correct

**Debug**:
```bash
# Check email config in Render logs
tail -f deployment.log | grep -i "email\|smtp"
```

### Test Data Not Being Created

**Problem**: Archive file is empty

**Solutions**:
1. Verify DATABASE_URL is correct
2. Check database is running and accessible
3. Verify migrations have been run
4. Check schools exist in database

**Debug**:
```bash
cd backend
python -c "
from app.core.database import SessionLocal
db = SessionLocal()
from app.models.models import School
print(f'Schools: {db.query(School).count()}')
db.close()
"
```

### GitHub Actions Fails

**Problem**: Workflow shows red ❌

**Solutions**:
1. Check all secrets are added to GitHub
2. Verify database secrets match actual database
3. Check PostgreSQL service is healthy
4. Review workflow logs for specific error

**Logs**:
1. Go to GitHub → Actions
2. Click "Daily Automated Test Faker"
3. Click failed run
4. Scroll down for error details

## Files

| File | Purpose |
|------|---------|
| `backend/populate_daily.py` | Main script - creates data, tests reports, archives |
| `.github/workflows/daily_faker.yml` | GitHub Actions scheduler - runs at 8 AM UTC |
| `backend/test_data_archive/` | Daily test data archives (JSON) |

## Performance Impact

- **Execution Time**: 5-10 minutes
- **Database Impact**: Minimal (only 50 new students + ~400 check-ins)
- **Storage**: ~50KB per day archive (~1.5MB/month)
- **Email**: Single HTML email per day

## Disabling the Scheduler

To temporarily disable automated runs:

1. Go to GitHub → `.github/workflows/daily_faker.yml`
2. Change the first line to: `# on:` (comment it out)
3. Commit changes

To re-enable:

1. Uncomment `on:` line
2. Commit and push

## Next Steps

✅ **Completed**:
- Automated daily data generation script
- GitHub Actions scheduler at 8 AM UTC
- Daily test data archival (30-day retention)
- Email reporting with HTML formatting

📋 **To Do**:
- [ ] Add SMTP credentials to Render environment
- [ ] Test first scheduled run (happens at 8 AM UTC)
- [ ] Verify email report arrives
- [ ] Download and review first archive

**Start**: Add SMTP credentials to Render, then wait for 8 AM UTC run tomorrow.

## Support

For issues:
1. Check workflow logs in GitHub Actions
2. Check Render deployment logs
3. Verify environment variables are set correctly
4. Run locally to debug: `python populate_daily.py`
