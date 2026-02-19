# Build In Public (BIP) Slack Rewards Bot

A Slack-based gamification system designed to encourage community participation through emoji-driven rewards, leaderboards, and redeemable prizes.

This bot was originally built to power a “Build In Public” program where students earned points for sharing work, engaging with peers, and completing structured activities. Points could then be redeemed for prizes, with full admin control over activities and rewards.

---

## 🚀 Overview

The BIP Slack Bot turns Slack reactions into structured, trackable achievements.

Users:
- Earn points via emoji reactions
- View weekly, monthly, and all-time leaderboards
- Track their personal activity history
- Redeem prizes using earned points

Admins:
- Create/edit/delete activities
- Define emoji → point mappings
- Control whether activities are admin-awarded
- Create/edit/delete prizes
- Adjust prize costs dynamically

All activity and prize data is persisted in PostgreSQL using SQLAlchemy ORM.

---

## 🧠 How It Works

### 1️⃣ Emoji-Based Activity Tracking

Each activity is mapped to:
- An emoji
- A point value
- A reward rule (who receives points)
- An optional admin restriction

When a user reacts to a message with a configured emoji:
- The bot validates the reaction
- Determines who should receive points
- Records the event in the database
- Sends a DM confirmation
- Updates point totals

Removing the reaction reverses the reward.

---

### 2️⃣ Slash Commands

| Command | Description |
|----------|-------------|
| `/bip_help` | Shows all available activities |
| `/bipweek` | Weekly leaderboard |
| `/bipmonth` | Monthly leaderboard |
| `/bipalltime` | All-time leaderboard |
| `/mybip` | Personal stats + activity history |
| `/claimprizes` | View and redeem prizes |

---

### 3️⃣ Admin Controls

Admins (email-based role check) can:

- Create new activities via Slack modal
- Edit existing activities
- Delete activities
- Create/edit/delete prizes
- Adjust point values
- Control whether rewards go to:
  - The reacting user
  - The original poster
  - Admin-awarded only

All admin interfaces are built using Slack modals and interactive components.

---

## 🏗 Architecture

**Event-driven Slack application using Socket Mode**

Core Components:

- `slack-bolt` for event handling
- SQLAlchemy ORM for relational modeling
- PostgreSQL for persistence
- Scoped session management for transactional safety
- Slack Block Kit for UI
- Role-based admin gating
- Reaction-based event processing

---

## 🗃 Data Model

### User
- Slack ID
- Name
- Email
- Activities (many-to-many)
- Prizes (many-to-many)

### Activity
- Emoji trigger
- Point value
- Description
- Admin-only flag
- Reward direction flag

### Prize
- Name
- Cost (points)
- Description
- Win message

### UserActivity
- Tracks each individual emoji claim
- Stores timestamp and message reference

### UserPrize
- Tracks prize redemptions

Point totals are calculated dynamically:
