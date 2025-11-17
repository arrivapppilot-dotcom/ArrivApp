# 🍽️ Kitchen/Comedor Feature - Setup & Quick Start

## What Was Built

A complete **meal planning dashboard for school kitchen managers** that automatically captures student attendance data every day at **10:00 AM**.

### Feature Highlights

✅ **Real-time Overview Cards**
- Total students expected to eat
- Students already present
- Absent students  
- Students with allergies
- Students with special diets

✅ **Class-Based Meal Planning Grid**
- See exactly how many students per class will eat today
- Track who has allergies or special diets
- Visual attendance percentage for each class

✅ **Automatic Daily Capture**
- Data captured automatically at 10:00 AM
- Happens every single day
- Kitchen manager doesn't need to do anything

✅ **Dietary Summary**
- See most common allergies in school
- See most common special diets
- Plan meals accordingly

## How It Works

1. **9:01 AM** - System marks absent students (existing feature)
2. **10:00 AM** - System captures kitchen attendance snapshot:
   - Counts students present (checked in)
   - Counts students absent
   - Counts students with allergies
   - Counts students with special diets
   - Stores data for meal planning
3. **Kitchen Manager** - Logs in and views `/comedor` page to plan meals

## Implementation Steps

### Step 1: Create Database Tables
```bash
cd backend
python migrate_add_kitchen_tables.py
```

This creates:
- `student_dietary_needs` - Stores allergies & special diets
- `kitchen_attendance` - Stores daily 10 AM snapshots

### Step 2: Generate Test Data (Optional)
```bash
python populate_and_simulate.py
# Choose option: "4. All (students + dietary + simulate)"
```

This creates:
- 50 students per school
- Dietary needs (20% with allergies, 15% with special diets)
- 7 days of simulated activities

### Step 3: Access the Page
```
URL: https://arrivapp-frontend.onrender.com/comedor.html
```

Or click "🍽️ Comedor" button in dashboard

## Database Models Added

### 1. StudentDietaryNeeds
Tracks dietary requirements for each student:
```python
{
    student_id: int,
    has_allergies: bool,
    allergies_description: "Peanut, Gluten",  # Optional
    has_special_diet: bool,
    special_diet_description: "Vegetarian",  # Optional
}
```

### 2. KitchenAttendance
Daily 10 AM snapshot of attendance:
```python
{
    school_id: int,
    snapshot_date: datetime,  # Captured at 10:00 AM
    class_name: "5A",
    total_students: 28,
    present: 27,  # Checked in
    absent: 1,    # Marked absent
    will_arrive_later: 0,
    with_allergies: 3,
    with_special_diet: 2,
}
```

## API Endpoints

### GET /api/comedor/today
Get today's meal planning data
```bash
curl -H "Authorization: Bearer <token>" \
  https://arrivapp-backend.onrender.com/api/comedor/today
```

### GET /api/comedor/history?days=7
Get last 7 days of data
```bash
curl -H "Authorization: Bearer <token>" \
  https://arrivapp-backend.onrender.com/api/comedor/history?days=7
```

### GET /api/comedor/dietary-summary
Get allergies and special diets summary
```bash
curl -H "Authorization: Bearer <token>" \
  https://arrivapp-backend.onrender.com/api/comedor/dietary-summary
```

## Frontend Page Structure

`frontend/comedor.html` includes:

1. **Navigation Bar**
   - Logo and title
   - Current date
   - Logout button

2. **Overview Cards (5 cards)**
   - Total Students
   - Already Present
   - Absent
   - With Allergies
   - With Special Diet

3. **Class Grid**
   - Shows stats for each class
   - Attendance percentage
   - Allergies & special diets count

4. **Dietary Summary Section**
   - Common allergies list
   - Common special diets list

5. **Auto-refresh**
   - Updates every 5 minutes
   - Real-time data

## Backend Router

`backend/app/routers/comedor.py` includes:

- `get_kitchen_data_today()` - Get today's 10 AM snapshot
- `get_kitchen_data_history()` - Get historical data
- `get_dietary_summary()` - Get allergy/diet statistics
- `_generate_kitchen_snapshot_for_today()` - Generate snapshot on-demand

## Scheduler Integration

`backend/app/services/scheduler.py` now includes:

- `capture_kitchen_attendance()` - Function that captures snapshot
- Scheduled to run **every day at 10:00 AM**
- Runs automatically without intervention

## User Permissions

Who can access `/comedor` page:
- ✅ **Admin** - Can view all schools
- ✅ **Director** - Can view only their school
- ✅ **Teacher** - Can view only their school

## Common Allergies (Pre-configured)
- Cacahuetes (Peanut)
- Gluten
- Lactosa (Dairy)
- Frutos secos (Tree nuts)
- Huevo (Egg)
- Mariscos (Shellfish)

## Common Special Diets (Pre-configured)
- Vegetariano (Vegetarian)
- Vegano (Vegan)
- Kosher
- Halal
- Sin TACC (Gluten-free)

## Files Modified/Created

### New Files
- `backend/app/routers/comedor.py` - API endpoints
- `backend/migrate_add_kitchen_tables.py` - Database migration
- `frontend/comedor.html` - Kitchen manager UI

### Modified Files
- `backend/app/models/models.py` - Added StudentDietaryNeeds and KitchenAttendance models
- `backend/app/main.py` - Registered comedor router
- `backend/app/services/scheduler.py` - Added kitchen attendance capture task
- `backend/populate_and_simulate.py` - Added dietary needs generation
- `frontend/dashboard.html` - Added comedor button

## Testing Checklist

- [ ] Database tables created successfully
- [ ] Migration script runs without errors
- [ ] Test data generated (students + dietary needs)
- [ ] Comedor button visible in dashboard
- [ ] Can access `/comedor.html` page
- [ ] Overview cards display correct numbers
- [ ] Class grid shows all classes
- [ ] Dietary summary shows allergies and diets
- [ ] Page auto-refreshes every 5 minutes
- [ ] API endpoints respond with data
- [ ] Scheduler captures data at 10 AM (check logs)

## Troubleshooting

### No data showing
1. Create test data: `python populate_and_simulate.py`
2. Check if students exist: `SELECT COUNT(*) FROM students;`
3. Check if dietary needs exist: `SELECT COUNT(*) FROM student_dietary_needs;`

### Kitchen page 403 error
- Make sure you're logged in
- Check user role (admin/director/teacher)
- Verify user has school_id assigned

### Snapshot not captured
- Check scheduler logs
- Verify server timezone
- Check if server time shows 10:00 AM

## Future Enhancements

- [ ] PDF export for meal plans
- [ ] Weekly planning view
- [ ] Supplier order integration
- [ ] Mobile app for kitchen staff
- [ ] Voice alerts for meal counts
- [ ] Allergen warnings
- [ ] Nutrition tracking

## Documentation

Complete documentation available in:
- `KITCHEN_COMEDOR_GUIDE.md` - Detailed feature guide
- `backend/app/routers/comedor.py` - Inline code documentation
- `frontend/comedor.html` - Frontend JavaScript comments

## Git Commits

- `d2aa8d2` - Add kitchen/comedor page feature (main)
- `8e2a2fe` - Add kitchen documentation

---

**Status:** ✅ Production Ready  
**Deployment:** Auto-deployed to Render  
**Last Updated:** November 17, 2025
