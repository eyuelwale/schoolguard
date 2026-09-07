# 🚀 SchoolGuard — Deployment Guide (Vercel & Supabase)

This guide provides step-by-step instructions for deploying **SchoolGuard** to production using **Supabase** (PostgreSQL Database), **Vercel** (React Frontend), and a containerized cloud host (such as **Render** or **Railway**) for the FastAPI backend and Telegram bot.

---

## 🏗️ Production Architecture

```mermaid
flowchart TD
    subgraph Cloud["🌐 Production Cloud Environment"]
        Vercel["⚡ Vercel (Frontend)\nReact + Vite SPA"]
        Host["🖥️ Render / Railway (Backend)\nFastAPI + Telegram Bot"]
        Supabase[("🐘 Supabase (Database)\nManaged PostgreSQL")]
        Telegram["🤖 Telegram API\nParent Push Alerts"]
    end

    User["📱 User (Phone / PC)"] -->|HTTPS| Vercel
    Vercel -->|REST API / JWT| Host
    Host -->|Connection Pooler (6543)| Supabase
    Host -->|Push Notifications| Telegram
    Telegram -->|Instant Alert| Parents["👨‍👩‍👧 Parents' Phones"]
```

| Component | Recommended Platform | Why? |
| :--- | :--- | :--- |
| **Database** | **Supabase** | Managed PostgreSQL, generous free tier, SSL security, built-in backups, connection pooling. |
| **Frontend** | **Vercel** | Global CDN edge network, instant builds for Vite/React, automatic HTTPS, zero-config SPA routing. |
| **Backend API & Bot** | **Render** or **Railway** | Runs continuous background processes (needed for FastAPI + Telegram Bot polling daemon). |

---

## 📌 Phase 1: Set Up Supabase Database

### 1. Create a Supabase Project
1. Go to [https://supabase.com](https://supabase.com) and sign in (or sign up with GitHub).
2. Click **New Project**.
3. Fill in:
   - **Name**: `schoolguard-db`
   - **Database Password**: *(Generate a strong password and save it in a safe place)*
   - **Region**: Choose a region closest to your users (e.g., `Frankfurt (eu-central-1)` or `East US`).
4. Click **Create new project** and wait 1–2 minutes for provisioning.

---

### 2. Run Database Schema in Supabase
You can initialize all SchoolGuard tables with one click:
1. In the Supabase sidebar, click **SQL Editor** (`>_` icon).
2. Click **+ New query**.
3. Open the file [`database/supabase_schema.sql`](file:///c:/Users/eyuel.wale/Desktop/schoolguard/database/supabase_schema.sql) in this repository, copy all its contents, and paste them into the Supabase SQL editor.
4. Click **Run** (or press `Ctrl + Enter`).
5. Open the **Table Editor** tab in the sidebar — you will see all 10 tables created:
   - `schools`, `users`, `classes`, `students`, `parent_students`, `attendance`, `attendance_events`, `notifications`, `notification_settings`, `registration_codes`.

---

### 3. Copy Your Supabase Connection String
1. In Supabase, go to **Project Settings** (gear icon) &rarr; **Database**.
2. Scroll to the **Connection string** section.
3. Select the **URI** tab.
4. Select **Session Pooler** (Port `5432`) or **Transaction Pooler** (Port `6543`):
   ```text
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```
5. Replace `[YOUR-PASSWORD]` with the database password you created in step 1.

---

## 📌 Phase 2: Deploy Backend & Telegram Bot (Render / Railway)

Because the Telegram Bot requires a **persistent background process**, we deploy the backend as a Web Service on **Render** (free) or **Railway**.

### Option A: Deploy with Render (Recommended)

1. Push your project code to a **GitHub** repository.
2. Go to [https://render.com](https://render.com) and sign in.
3. Click **New +** &rarr; select **Web Service**.
4. Connect your GitHub repository.
5. Configure the settings:
   - **Name**: `schoolguard-api`
   - **Runtime**: `Python 3`
   - **Region**: Same region as your Supabase database.
   - **Branch**: `main`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
     ```
6. Scroll down to **Environment Variables** and add:
   | Key | Value |
   | :--- | :--- |
   | `DATABASE_URL` | Your Supabase connection string from Phase 1 (`postgresql+psycopg2://...`) |
   | `SECRET_KEY` | A random 32-character string (e.g. `your-super-secret-jwt-key-here-32chars`) |
   | `ENVIRONMENT` | `production` |
   | `CORS_ORIGINS` | `https://*.vercel.app` (or your Vercel frontend URL once created) |
   | `TELEGRAM_BOT_TOKEN` | Your Telegram Bot token from `@BotFather` |
   | `TELEGRAM_BOT_USERNAME` | Your Telegram Bot username (e.g. `YourSchoolGuardBot`) |
   | `TIMEZONE` | `Africa/Addis_Ababa` |

7. Click **Create Web Service**. Render will install dependencies and start your API.
8. Once deployed, Render will provide your public API URL:
   ```text
   https://schoolguard-api.onrender.com
   ```

---

### Running the Telegram Bot on Render (Background Worker)
1. On Render, click **New +** &rarr; **Background Worker**.
2. Connect the same repository.
3. Set **Start Command**:
   ```bash
   python -m backend.bot.main
   ```
4. Add the same Environment Variables (`DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, etc.).
5. Click **Create Background Worker**. The bot will now poll 24/7 without interruption.

---

## 📌 Phase 3: Deploy Frontend to Vercel

### 1. Import Project to Vercel
1. Go to [https://vercel.com](https://vercel.com) and sign in with GitHub.
2. Click **Add New...** &rarr; **Project**.
3. Select your `schoolguard` repository and click **Import**.

---

### 2. Configure Vercel Project Settings
On the import screen, configure the following:

- **Framework Preset**: `Vite`
- **Root Directory**: Click **Edit** and choose `frontend`.
- **Build Command**: `npm run build` *(auto-detected)*
- **Output Directory**: `dist` *(auto-detected)*

---

### 3. Add Environment Variable
Under **Environment Variables**, add:
| Name | Value |
| :--- | :--- |
| `VITE_API_URL` | Your Render backend URL (e.g. `https://schoolguard-api.onrender.com`) |

> [!IMPORTANT]
> Do **NOT** add a trailing slash to `VITE_API_URL`.  
> Correct: `https://schoolguard-api.onrender.com`  
> Incorrect: `https://schoolguard-api.onrender.com/`

---

### 4. Deploy
1. Click **Deploy**.
2. Vercel will build your React application in ~30 seconds.
3. Once finished, Vercel gives you your live production URL:
   ```text
   https://schoolguard.vercel.app
   ```
4. SPA routing is pre-configured via `frontend/vercel.json` so refreshing pages or deep links will never produce 404 errors.

---

## 📌 Phase 4: Bootstrap Initial Admin on Production

Once your frontend and backend are live:
1. Open your Vercel production URL: `https://schoolguard.vercel.app`.
2. Click the link **"Bootstrap Initial Admin"** below the login form.
3. Enter:
   - **Full Name**: `System Admin`
   - **Email / Username**: `admin@schoolguard.local`
   - **Password**: `YourSecurePassword123!`
4. Click **Bootstrap Initial Admin**.
5. Switch back to **Login** and sign in!

---

## 📌 Phase 5: Verification Checklist

- [ ] **Database Connectivity**: Open `https://schoolguard-api.onrender.com/health` in your browser. It should return `{"status":"healthy"}`.
- [ ] **Frontend Loading**: Open `https://schoolguard.vercel.app` on both your PC and your smartphone.
- [ ] **Authentication**: Log in with your new admin credentials.
- [ ] **Telegram Bot**: Open Telegram on your phone, find your bot, send `/start`, and verify it responds.
- [ ] **Live Push Notification**: In the portal, register an arrival or roll call for a linked student and verify that the parent receives the Telegram notification on their phone within 2 seconds.

---

## 💡 Summary of Environment Variables

### Backend (`Render` or `Railway`):
```ini
DATABASE_URL=postgresql+psycopg2://postgres.[REF]:[PASS]@[HOST]:6543/postgres?sslmode=require
SECRET_KEY=generate_a_random_jwt_secret_key_here
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend.vercel.app,https://*.vercel.app
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuvWXyz
TELEGRAM_BOT_USERNAME=YourSchoolGuardBot
TIMEZONE=Africa/Addis_Ababa
DEFAULT_SCHOOL_START=08:00:00
DEFAULT_SCHOOL_END=16:00:00
```

### Frontend (`Vercel`):
```ini
VITE_API_URL=https://your-backend.onrender.com
```
