# Database Migrations

Database schema management for StormGuard Phase 1-4.

## Migration Files

### Phase 1: User Management (001_phase1_user_management.sql)
Created tables:
- `users` - User accounts with location and preferences
- `user_preferences` - Alert preferences per user
- `alerts` - Disaster alerts sent to users
- `chat_messages` - Chat history with RAG context

## Running Migrations

### Option 1: Using Python SQLAlchemy (Recommended)

Initialize database tables automatically:

```bash
python data_pipeline/init_db.py init
```

### Option 2: Using SQL Script with psql

Connect to PostgreSQL and run the migration:

```bash
psql -h localhost -U airflow -d airflow -f data_pipeline/migrations/001_phase1_user_management.sql
```

## Database Schema

### users Table
- `id` (UUID): Primary key
- `email` (VARCHAR): Unique email address
- `full_name` (VARCHAR): User's full name
- `latitude` (DECIMAL): Geographic latitude
- `longitude` (DECIMAL): Geographic longitude
- `city` (VARCHAR): City name
- `country` (VARCHAR): Country name
- `timezone` (VARCHAR): IANA timezone
- `interests` (TEXT): Comma-separated disaster types
- `notification_enabled` (BOOLEAN): Enable/disable alerts
- `notification_token` (TEXT): Firebase FCM device token
- `created_at` (TIMESTAMP): Account creation time
- `updated_at` (TIMESTAMP): Last update time
- `last_login` (TIMESTAMP): Last login time

### user_preferences Table
- `user_id` (UUID FK): References users.id
- `hurricane_alerts` (BOOLEAN): Enable hurricane alerts
- `heat_wave_alerts` (BOOLEAN): Enable heat wave alerts
- `flood_alerts` (BOOLEAN): Enable flood alerts
- `severe_storm_alerts` (BOOLEAN): Enable severe storm alerts
- `min_risk_level` (VARCHAR): Minimum risk level (LOW/MEDIUM/HIGH/CRITICAL)
- `alert_radius_km` (INT): Alert radius in kilometers
- `max_daily_alerts` (INT): Maximum alerts per day
- `quiet_hours_start` (VARCHAR): Start of quiet hours (HH:MM)
- `quiet_hours_end` (VARCHAR): End of quiet hours (HH:MM)
- `enable_push` (BOOLEAN): Enable push notifications
- `enable_email` (BOOLEAN): Enable email notifications
- `enable_sms` (BOOLEAN): Enable SMS notifications
- `updated_at` (TIMESTAMP): Last update time

### alerts Table
- `id` (UUID): Primary key
- `user_id` (UUID FK): References users.id
- `disaster_type` (VARCHAR): Type of disaster
- `title` (VARCHAR): Alert title
- `message` (TEXT): Alert message body
- `risk_level` (VARCHAR): Risk severity level
- `risk_score` (DECIMAL): Risk score 0-1
- `latitude` (DECIMAL): Location latitude
- `longitude` (DECIMAL): Location longitude
- `radius_km` (INT): Impact radius
- `sent` (BOOLEAN): Has alert been sent
- `read` (BOOLEAN): Has user read alert
- `clicked` (BOOLEAN): Did user click alert
- `created_at` (TIMESTAMP): Creation time
- `sent_at` (TIMESTAMP): Send time
- `read_at` (TIMESTAMP): Read time

### chat_messages Table
- `id` (UUID): Primary key
- `user_id` (UUID FK): References users.id
- `user_message` (TEXT): User's message
- `assistant_response` (TEXT): AI assistant response
- `sources` (JSON): Array of source documents used
- `session_id` (VARCHAR): Conversation session ID
- `tokens_used` (INT): LLM tokens used for response
- `created_at` (TIMESTAMP): Message timestamp

## Indexes

Performance indexes created on:
- `users.email` - Fast user lookup by email
- `users(latitude, longitude)` - Geographic queries
- `alerts.user_id` - Quick alert retrieval per user
- `alerts.disaster_type` - Filter alerts by type
- `chat_messages.user_id` - Chat history per user
- `chat_messages.session_id` - Conversation sessions

## Triggers

Automatic timestamp management:
- `users_updated_at_trigger` - Updates `updated_at` on user changes
- `preferences_updated_at_trigger` - Updates `updated_at` on preference changes

## Resetting Database (Development Only)

⚠️ **WARNING**: This will delete all data!

```bash
python data_pipeline/init_db.py reset
```

Or manually:

```bash
python data_pipeline/init_db.py drop
python data_pipeline/init_db.py init
```

## Connecting to Database

### From Docker Compose

```bash
docker-compose exec postgres psql -U airflow -d airflow
```

### From Local

```bash
psql -h localhost -U airflow -d airflow -p 5432
```

Connection string:
```
postgresql://airflow:airflow@postgres:5432/airflow
```

## Verifying Migrations

Check tables exist:

```sql
\dt
```

Check table schema:

```sql
\d users
\d user_preferences
\d alerts
\d chat_messages
```

## Phase 2-4 Migrations

Future migrations will add:
- Phase 2: RAG vector embeddings table (Pinecone setup)
- Phase 3: Push notification status tracking
- Phase 4: WebSocket session management
