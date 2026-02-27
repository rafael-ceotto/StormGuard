# UI Testing Guide - User Registration & Notifications

Complete manual testing guide for the StormGuard web interface with user registration and push notifications.

## 📋 Pre-Test Checklist

Before starting, ensure:
- [ ] API running on http://localhost:8000
- [ ] chat.html is accessible at http://localhost:8000
- [ ] Database is operational (PostgreSQL)
- [ ] Redis is running (for caching)
- [ ] Firebase credentials configured
- [ ] Browser supports notifications (Chrome, Firefox, Safari, Edge)

## 🧪 Test 1: User Registration Flow

### Step 1.1: Open the Application

1. Open browser: **http://localhost:8000**
2. You should see:
   - ✓ Login modal appears
   - ✓ "Don't have an account?" link visible
   - ✓ Registration form option

<img src="assets/registration-modal.png" alt="Registration modal" width="400"/>

### Step 1.2: Click "Register" / "Create Account"

1. Click the registration link
2. Verify form fields appear:
   - [ ] Email input
   - [ ] Password input
   - [ ] Full Name input
   - [ ] Phone number (optional)
   - [ ] Location input (for geo-alerts)
   - [ ] Timezone selector
   - [ ] "Register" button

### Step 1.3: Fill Registration Form

Enter the following test data:

```
Email:        test-user-#{timestamp}@stormguard.local
Password:     StormGuard123!@Test
Full Name:    Test User QA
Phone:        +1 (555) 123-4567
Location:     Miami, Florida
Timezone:     America/New_York
```

**Important**: Use unique email per test (add timestamp)

### Step 1.4: Submit Registration

1. Click "Register" button
2. Expected behavior:
   - ✓ Form validation passes
   - ✓ No error messages
   - ✓ Smooth loading state
   - ✓ Modal closes after 2-3 seconds
   - ✓ User redirected to main chat interface

<img src="assets/registration-success.png" alt="Registration success" width="400"/>

### Step 1.5: Verify User is Logged In

After registration, verify:
1. ✓ User name appears in header/profile
2. ✓ Chat interface is visible
3. ✓ localStorage contains access_token
4. ✓ No errors in browser console (F12)

**Check localStorage:**
```javascript
// In browser console:
localStorage.getItem('access_token')    // Should have JWT token
localStorage.getItem('user_id')         // Should have UUID
```

## 🔔 Test 2: Push Notifications Setup

### Step 2.1: Request Notification Permission

After successful login:

1. You should see a browser notification prompt
2. Click **"Allow"** to grant permissions
3. Expected result:
   - ✓ Browser stores notification token
   - ✓ Token sent to StormGuard API
   - ✓ User profile updated with device token

**Chrome/Firefox/Edge:**
- Look for notification icon in address bar
- Click to grant permissions
- You may need to check "Remember this choice"

### Step 2.2: Configure Notification Preferences

1. Look for "Settings" or "Preferences" button in the UI
2. Should see notification preferences:
   - [ ] Push notifications (toggle)
   - [ ] Email notifications (toggle)
   - [ ] SMS notifications (toggle)
   - [ ] Disaster type preferences:
     - [ ] Hurricane alerts
     - [ ] Heat wave alerts
     - [ ] Flood alerts
     - [ ] Severe storm alerts
     - [ ] Tornado alerts
     - [ ] Wildfire alerts
   - [ ] Minimum risk level:
     - [ ] LOW (0.30)
     - [ ] MEDIUM (0.60)
     - [ ] HIGH (0.80)
     - [ ] CRITICAL (0.95)
   - [ ] Quiet hours (e.g., 22:00 - 08:00)

3. Configure test settings:
```
Push Notifications:  ON
Hurricane Alerts:    ON
Heat Wave Alerts:    ON
Flood Alerts:        OFF
Min Risk Level:      MEDIUM
Quiet Hours:         22:00 - 08:00
```

4. Click "Save Preferences"
5. Verify success message appears

### Step 2.3: Verify Profile in Database

Open a terminal and verify the user was created:

```bash
# Connect to database
psql -U postgres -d stormguard

# Query the user
SELECT id, email, full_name, location, notification_enabled, notification_token 
FROM users 
WHERE email = 'test-user-XXXX@stormguard.local' 
LIMIT 1;
```

Expected output:
```
id                  | UUID
email               | test-user-XXXX@stormguard.local
full_name           | Test User QA
location            | Miami, Florida
notification_enabled| true
notification_token  | (24-char browser token)
```

## 📱 Test 3: Trigger Test Alert

### Step 3.1: Send Test Alert via API

Open another terminal and send a test alert to your registered user:

```bash
# Get your user ID from database
USER_EMAIL="test-user-XXXX@stormguard.local"
USER_ID=$(psql -U postgres -d stormguard -t -c \
  "SELECT id FROM users WHERE email='$USER_EMAIL' LIMIT 1;")

echo "User ID: $USER_ID"

# Set your API token (or use a valid JWT)
TOKEN="your-api-token-here"

# Send test alert
curl -X POST http://localhost:8000/api/v1/alerts/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_ids\": [\"$USER_ID\"],
    \"disaster_type\": \"hurricane\",
    \"title\": \"🌀 Hurricane Alert - Test\",
    \"message\": \"A strong hurricane is approaching Miami. Prepare immediately!\",
    \"risk_level\": \"CRITICAL\",
    \"risk_score\": 0.92,
    \"latitude\": 25.7617,
    \"longitude\": -80.1918,
    \"radius_km\": 150
  }"
```

Expected response:
```json
{
  "sent": 1,
  "failed": 0,
  "timestamp": "2024-02-27T14:30:00Z"
}
```

### Step 3.2: Verify Notification Appears

After sending alert:

1. **In-app notification**:
   - ✓ Alert appears in "Alerts" panel on left sidebar
   - ✓ Unread badge shows (typically red dot)
   - ✓ Alert displays:
     - Title: "🌀 Hurricane Alert - Test"
     - Risk level indicator (red/orange/yellow)
     - Location: Miami, Florida
     - Risk score: 92%

2. **Browser push notification**:
   - ✓ Push notification appears in bottom-right
   - ✓ Shows title and truncated message
   - ✓ Clicking it focuses the browser window

3. **Database verification**:
```sql
SELECT id, disaster_type, risk_score, read_at, clicked_at, created_at 
FROM alerts 
WHERE user_id = 'YOUR_USER_ID' 
ORDER BY created_at DESC 
LIMIT 1;
```

Expected: `read_at` and `clicked_at` are NULL (user hasn't interacted yet)

### Step 3.3: Click Alert to Interact

1. Click the alert in the UI or push notification
2. Expected behavior:
   - ✓ Alert expands to show full details
   - ✓ Message is fully visible
   - ✓ User is marked as "clicked" in database

Verify in database:
```sql
SELECT id, disaster_type, read_at, clicked_at 
FROM alerts 
WHERE user_id = 'YOUR_USER_ID' 
ORDER BY created_at DESC 
LIMIT 1;
-- clicked_at should now have a timestamp
```

### Step 3.4: Mark Alert as Read

1. Open the alert panel
2. The alert should automatically mark as read when visible
3. Or click "Mark as read" button if present

Verify:
```sql
SELECT read_at FROM alerts WHERE user_id = 'YOUR_USER_ID' LIMIT 1;
-- Should have a timestamp
```

## 💬 Test 4: Chat Functionality

### Step 4.1: Send Chat Message

1. Click on the chat input field
2. Type a test question:
   ```
   What should I do to prepare for a hurricane in Miami?
   ```

3. Press Enter or click "Send"
4. Expected behavior:
   - ✓ Message appears in chat instantly
   - ✓ Message has user avatar/name on right
   - ✓ Loading indicator appears
   - ✓ AI response arrives within 5 seconds

### Step 4.2: Verify AI Response

The AI should respond with:
- ✓ Relevant disaster preparation advice
- ✓ References to knowledge base (sources)
- ✓ Actionable steps
- ✓ Message appears on left (AI side)

Example response:
```
To prepare for a hurricane in Miami:

1. Secure your property
   - Board up windows
   - Stock supplies (water, food, medications)
   
2. Evacuation plan
   - Know your zone
   - Have backup routes
   
3. Stay informed
   - Monitor official alerts
   - Follow local guidance

Sources: Hurricane Preparedness Guide, NOAA Emergency Response, Miami-Dade County Safety
```

### Step 4.3: Multiple Messages

Send several follow-up messages to verify:
1. ✓ Chat history persists
2. ✓ Conversation context is maintained
3. ✓ Old messages remain visible
4. ✓ Session ID is consistent

## 🔍 Test 5: Error Handling

### Test 5.1: Invalid Login

Attempt login with invalid credentials:

```
Email:    nonexistent@test.com
Password: WrongPassword
```

Expected:
- ✓ Error message appears
- ✓ No access token issued
- ✓ User stays on login modal

### Test 5.2: Weak Password

Attempt registration with weak password:

```
Email:    test@example.com
Password: 123
```

Expected:
- ✓ Validation error on password field
- ✓ Clear message: "Password must be at least 8 characters"
- ✓ Registration button disabled

### Test 5.3: Duplicate Email

Attempt registration with existing email:

```
Email:    test-user-XXXX@stormguard.local  (already registered)
```

Expected:
- ✓ Error message: "Email already registered"
- ✓ Clear CTA to login instead
- ✓ Login button offered

### Test 5.4: Network Error Simulation

1. Open DevTools (F12)
2. Go to Network tab
3. Simulate offline: Right-click → "Throttling" → "Offline"
4. Try to send a message
5. Expected:
   - ✓ Error message appears
   - ✓ Retry button shown
   - ✓ No crash or blank screen

## 📊 Test 6: Responsive Design

Test on multiple screen sizes:

### Desktop (1920x1080)
- [ ] 3-column layout visible (alerts, chat, stats)
- [ ] All buttons clickable
- [ ] No overflow
- [ ] Text readable

### Tablet (768x1024)
- [ ] 2-column layout (alerts + chat, stats below)
- [ ] Touch targets are 44px minimum
- [ ] Scrolling works smoothly

### Mobile (375x667)
- [ ] Single column layout
- [ ] Hamburger menu appears
- [ ] Bottom navigation tabs
- [ ] All content accessible

## 🐛 Test 7: Browser Console Check

After all tests, check browser console for errors:

1. Press **F12** to open DevTools
2. Go to **Console** tab
3. Expected:
   - ✓ No red errors
   - ✓ WebSocket connected message
   - ✓ Auth token loaded
   - ✓ Only yellow warnings (non-critical)

Example good console:
```
✓ WebSocket connected: ws://localhost:8000/api/v1/ws
✓ User authenticated: test-user@example.com
✓ Alerts polling enabled (30s)
⚠ (Warning: minor deprecation notice - OK to ignore)
```

## 📋 Test Results Checklist

### Registration
- [ ] Form displays correctly
- [ ] Validation works
- [ ] User is created in database
- [ ] Access token is issued
- [ ] localStorage is populated

### Notifications
- [ ] Permission prompt appears
- [ ] Browser allows permissions
- [ ] Device token is registered
- [ ] Preferences page loads
- [ ] Settings can be saved

### Alert Delivery
- [ ] Test alert is sent via API
- [ ] In-app alert appears
- [ ] Push notification triggers
- [ ] Alert database record created
- [ ] Read/click tracking works

### Chat
- [ ] Messages send successfully
- [ ] AI responses are relevant
- [ ] History persists
- [ ] WebSocket connection stable

### UI/UX
- [ ] No layout breaks
- [ ] Responsive design works
- [ ] Buttons all clickable
- [ ] Forms provide feedback
- [ ] Loading states visible

### Error Handling
- [ ] Invalid input rejected
- [ ] Network errors handled
- [ ] Error messages are clear
- [ ] No console errors

## 🎯 Success Criteria

✅ **PASS** if:
- [x] User can register
- [x] Notifications permission granted
- [x] Alert received and displayed
- [x] Chat functionality works
- [x] No JavaScript errors
- [x] Responsive on all devices
- [x] Database records created
- [x] Performance is acceptable (<5s responses)

❌ **FAIL** if:
- [x] Registration errors
- [x] Notifications don't work
- [x] Alerts not delivered
- [x] Chat doesn't respond
- [x] Console has errors
- [x] Layout breaks on mobile
- [x] Database not updated
- [x] Response times > 10s

---

**Testing Duration**: ~30 minutes
**Test Date**: _______________
**Tester**: _______________
**Pass/Fail**: _______________
**Issues Found**: 
```




```

**Sign-off**: _______________
