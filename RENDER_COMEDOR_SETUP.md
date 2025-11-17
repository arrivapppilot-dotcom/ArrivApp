# 🍽️ Adding Comedor User to Render Database

The comedor user needs to be added to your **Render PostgreSQL database**, not your local database.

## Quick Steps

### Option 1: Using Render Database Console (Easiest)

1. Go to **Render Dashboard** → **PostgreSQL Database** → **Connect** tab
2. Copy the **PSQL Command** (it looks like: `psql postgresql://user:pass@host/db`)
3. Run it in your terminal to connect to Render database
4. Execute this SQL:

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

**Note:** Replace `2` with the actual school ID from Render database. To find it:
```sql
SELECT id, name FROM schools WHERE is_active = true LIMIT 1;
```

---

### Option 2: Using Python Script (Recommended)

1. Get your Render database URL from Render Dashboard
   - Go to **PostgreSQL** → **Connect** → Copy the connection string
   - It looks like: `postgresql://user:password@host.render.com:5432/database`

2. Run the script:
```bash
cd backend
python add_comedor_to_render.py "postgresql://user:password@host.render.com:5432/database" "School Name" "kitchen2025"
```

Example:
```bash
python add_comedor_to_render.py "postgresql://render_user:xyz@oregon-postgres.render.com:5432/arrivapp" "Colegio San José" "kitchen2025"
```

---

### Option 3: Via Render Shell

1. Go to **Render Dashboard** → **Your Backend Service** → **Shell** tab
2. Run:
```bash
cd backend
python add_comedor_to_render.py $DATABASE_URL "School Name" "kitchen2025"
```

The `$DATABASE_URL` environment variable is automatically available in Render shell.

---

## Verify the User Was Created

After creating the user, test the login:

```bash
curl -X POST https://arrivapp-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"comedor","password":"kitchen2025"}'
```

You should get a response with an `access_token`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "User 'comedor' already exists" | The user is already in the database. Try a different password or delete and recreate. |
| "School not found" | Make sure the school name exactly matches a school in Render database. Use the SQL to check names. |
| Connection refused | Check that your DATABASE_URL is correct and you have network access to Render. |
| Permission denied | Make sure you're using the correct PostgreSQL credentials from Render. |

---

## Once Created

After the comedor user is in Render database:

1. Go to https://arrivapp-frontend.onrender.com/login.html
2. Enter:
   - Username: `comedor`
   - Password: `kitchen2025`
3. You'll be redirected to `/comedor` page ✅

---

## Alternative: Add via Render Web Console

If you prefer the web interface:
1. Render Dashboard → PostgreSQL → **Query** tab
2. Paste the SQL from Option 1
3. Execute
