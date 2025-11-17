# 🍽️ Quick Setup: Add Comedor User via Render Shell

## Easiest Method - Render Shell (2 minutes)

1. Go to **Render Dashboard** → Your **Backend Service** (arrivapp-backend)
2. Click the **"Shell"** tab at the top
3. You'll get a terminal connected to your Render instance
4. Run this command:

```bash
python backend/quick_add_comedor.py
```

That's it! The comedor user will be created automatically in your Render database.

---

## Verify It Works

After running the script, go to:
**https://arrivapp-frontend.onrender.com/login.html**

Login with:
- Username: `comedor`
- Password: `kitchen2025`

You should be redirected to `/comedor` page! ✅

---

## What If the Script Fails?

If you get an error, check:

1. **Database connection issue?**
   - Make sure Render backend is running (check Logs tab)
   - DATABASE_URL environment variable is set

2. **User already exists?**
   - The script checks and will tell you

3. **No active schools?**
   - Make sure you have at least one school with is_active=true

---

## Alternative: Manual SQL (If Shell Doesn't Work)

Go to your **PostgreSQL database** in Render → **Browser** or **Query** tab

Paste this SQL:

```sql
SELECT id, name FROM schools WHERE is_active = true LIMIT 1;
```

Note the school ID (let's say it's 2), then run:

```sql
INSERT INTO users (email, username, hashed_password, full_name, is_active, is_admin, role, school_id, created_at)
VALUES (
  'comedor@example.com',
  'comedor',
  '$2b$12$BFFXGm9ryC1eoSeIoxwyLuhsuoOvmltNnaxrOg7w/WPbr9srNnveq',
  'Kitchen Manager',
  true,
  false,
  'comedor',
  2,
  NOW()
);
```

Replace `2` with your actual school ID.

---

## Next Steps

Once comedor is created:
- ✅ Login as comedor user
- ✅ Verify /comedor page loads
- ✅ Check that back button is hidden
- ✅ Verify can't access dashboard or other pages
