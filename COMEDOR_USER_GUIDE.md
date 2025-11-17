# 🍽️ Comedor User Role - Quick Start Guide

## Overview

The **comedor** role is a new specialized user profile that gives **kitchen managers restricted access to ONLY the `/comedor` page** for meal planning and dietary management. This role cannot access any other pages in the system.

## Features

### Comedor Role Access
- ✅ Access to `/comedor` (Kitchen Manager Dashboard)
- ✅ View meal planning data for all classes
- ✅ View dietary requirements (allergies, special diets)
- ✅ View attendance statistics
- ✅ Automatic data capture at 10 AM daily
- ❌ No access to dashboard, student management, or admin panels

### User Restrictions
- Cannot navigate to other pages
- Cannot access admin/management features
- Logged in only to assigned school
- Cannot see students, teachers, or other sensitive data

## Creating a Comedor User

### Method 1: Using the Creation Script (Recommended for Render)

```bash
cd /Users/lucaalice/Desktop/AI\ projects/ArrivApp/backend

# Create comedor user for first active school with default password
python create_comedor_user.py

# Create comedor user for specific school with custom password
python create_comedor_user.py "Your School Name" "custom_password"
```

**Default Credentials** (if not specified):
- Username: `comedor`
- Password: `comedor123`
- Email: `comedor@example.com`
- School: First active school in database
- Role: comedor

### Method 2: Direct Database Entry

```sql
-- Using psql or your database client
INSERT INTO users (email, username, hashed_password, full_name, is_active, is_admin, role, school_id, created_at)
VALUES (
  'kitchen-manager@school.com',
  'kitchen_manager_1',
  '<hashed_password>',
  'Kitchen Manager Name',
  true,
  false,
  'comedor',
  <school_id>,
  NOW()
);
```

## Deployment to Render

### Steps to Add Comedor User on Render:

1. **Connect to Render PostgreSQL Database**
   ```bash
   # Get database connection string from Render dashboard
   psql <your_render_postgres_url>
   ```

2. **Create the User**
   - Option A: Use the Python script via Render shell
   - Option B: Run SQL directly in Render database console

3. **Verify Creation**
   ```sql
   SELECT username, role, school_id FROM users WHERE role = 'comedor';
   ```

## Login Instructions

1. Go to login page: https://arrivapp-frontend.onrender.com/login.html
2. Enter credentials:
   - Username: `comedor` (or custom username)
   - Password: `comedor123` (or custom password)
3. Click Login
4. User will be redirected directly to `/comedor` page
5. Navigation back to dashboard NOT available (no back button)

## User Behavior

### What Comedor Users See
- Real-time meal planning data
- Class-by-class attendance breakdown
- Dietary requirements summary
- Automatic 10 AM daily snapshots
- 5-minute auto-refresh of data

### What Comedor Users Cannot Do
- Access any page except `/comedor`
- View student details beyond meal planning
- Manage users or schools
- Access admin features
- Export or download data
- Add/remove students

## Security Notes

- Comedor role has **minimal permissions** - only comedor endpoints are accessible
- No back button in header for comedor users
- Cannot navigate to other pages even if URL is manually changed
- Session restricted to assigned school only
- All data access filtered by school_id

## API Endpoints Available to Comedor

- `GET /api/comedor/today` - Today's meal planning data
- `GET /api/comedor/history?days=7` - Historical data (default 7 days, max 90)
- `GET /api/comedor/dietary-summary` - Dietary requirements summary

## Modifying Comedor User

### Change Password
```sql
UPDATE users 
SET hashed_password = '<new_hashed_password>'
WHERE username = 'comedor';
```

### Change School Assignment
```sql
UPDATE users 
SET school_id = <new_school_id>
WHERE username = 'comedor';
```

### Deactivate User
```sql
UPDATE users 
SET is_active = false
WHERE username = 'comedor';
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't login as comedor | Check if user exists in database: `SELECT * FROM users WHERE username='comedor'` |
| "Insufficient permissions" error | Verify role is set to `comedor` in database |
| Cannot access `/comedor` page | Check if school_id is assigned: `SELECT school_id FROM users WHERE username='comedor'` |
| Back button visible | Check user role - back button only shows for admin/director |
| Data not loading | Verify user has correct school_id and school is active |

## Future Enhancements

- [ ] Email notifications for comedor users
- [ ] Meal planning history export (PDF/CSV)
- [ ] Custom alerts for dietary issues
- [ ] Multi-language support
- [ ] Mobile-optimized dashboard

---

**Role Hierarchy**
```
admin (full access) 
  ├── director (school management + comedor)
  ├── teacher (classes + comedor)
  └── comedor (comedor only) ✨ NEW
```

