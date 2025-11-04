# Frontend Integration Guide - Mazzaly Mini App

Complete guide for integrating Mazzaly Telegram Mini App with the backend API.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Telegram Mini App Setup](#telegram-mini-app-setup)
3. [Authentication Flow](#authentication-flow)
4. [Email Connection](#email-connection)
5. [Telegram Account Linking](#telegram-account-linking)
6. [API Reference](#api-reference)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

---

## 🎯 Overview

The Mazzaly Mini App supports three authentication methods:

| Method | Description | Use Case |
|--------|-------------|----------|
| **Telegram** | Login via Telegram InitData | First-time users opening Mini App |
| **Email** | Link email to Telegram account | Users who want email notifications |
| **Web-to-Telegram** | Link existing web account to Telegram | Existing users who want to use Mini App |

---

## 🚀 Telegram Mini App Setup

### 1. Initialize Telegram WebApp

Add this to your HTML `<head>`:

```html
<script src="https://telegram.org/js/telegram-web-app.js"></script>
```

### 2. Get InitData

```javascript
// Check if running in Telegram
if (window.Telegram && window.Telegram.WebApp) {
  const tg = window.Telegram.WebApp;
  
  // Get InitData (automatically signed by Telegram)
  const initData = tg.initData;
  
  // Optional: Get user info
  const user = tg.initDataUnsafe.user;
  console.log('User:', user);
  
  // Expand Mini App to full height
  tg.expand();
  
  // Ready
  tg.ready();
}
```

### 3. Authenticate with Backend

Send `initData` to backend for validation:

```javascript
async function loginWithTelegram() {
  const tg = window.Telegram.WebApp;
  const initData = tg.initData;
  
  if (!initData) {
    console.error('Not running in Telegram Mini App');
    return;
  }
  
  try {
    const response = await fetch('https://api.mazzaly.uz/api/telegram-auth/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        init_data: initData
      })
    });
    
    if (!response.ok) {
      throw new Error('Authentication failed');
    }
    
    const data = await response.json();
    
    // Save tokens
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    
    // Save user info
    localStorage.setItem('user', JSON.stringify(data.user));
    
    console.log('Logged in:', data.user);
    
    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}
```

---

## 🔐 Authentication Flow

### Login Flow Diagram

```
User Opens Mini App
       ↓
Get initData from Telegram SDK
       ↓
POST /api/telegram-auth/ with initData
       ↓
Backend validates initData
       ↓
If valid → Return JWT tokens + user info
       ↓
Store tokens in localStorage
       ↓
Use access token for API requests
```

### Request Format

**Endpoint:** `POST /api/telegram-auth/`

**Request Body:**
```json
{
  "init_data": "query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A279058397..."
}
```

**Success Response (200):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 123,
    "email": null,
    "telegram_id": "279058397",
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "login_method": "telegram",
    "is_email_verified": false
  }
}
```

**Error Response (400):**
```json
{
  "detail": "Invalid init_data"
}
```

---

## ✉️ Email Connection

Allow users to link their email address to receive notifications and enable multi-platform access.

### Step 1: Send OTP to Email

```javascript
async function sendOTP(email) {
  const accessToken = localStorage.getItem('access_token');
  
  try {
    const response = await fetch('https://api.mazzaly.uz/api/mini-app/auth/connect-email/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': accessToken  // No "Bearer " prefix needed
      },
      body: JSON.stringify({
        email: email
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to send OTP');
    }
    
    const data = await response.json();
    console.log('OTP sent:', data);
    
    return data;
  } catch (error) {
    console.error('Send OTP error:', error);
    throw error;
  }
}
```

**Endpoint:** `POST /api/mini-app/auth/connect-email/`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "message": "OTP sent successfully",
  "email": "user@example.com",
  "expires_in": 300
}
```

**Error Responses:**
- `400`: Email already linked
- `401`: Invalid or missing token

### Step 2: Verify OTP

```javascript
async function verifyOTP(email, otp) {
  const accessToken = localStorage.getItem('access_token');
  
  try {
    const response = await fetch('https://api.mazzaly.uz/api/mini-app/auth/OTP/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': accessToken
      },
      body: JSON.stringify({
        email: email,
        otp: otp
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Invalid OTP');
    }
    
    const data = await response.json();
    
    // Update stored user info
    localStorage.setItem('user', JSON.stringify(data.user));
    
    console.log('Email linked successfully:', data.user);
    
    return data;
  } catch (error) {
    console.error('Verify OTP error:', error);
    throw error;
  }
}
```

**Endpoint:** `POST /api/mini-app/auth/OTP/`

**Request:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Success Response (200):**
```json
{
  "access": "eyJhbGci...",
  "refresh": "eyJhbGci...",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "telegram_id": "279058397",
    "login_method": "both",
    "is_email_verified": true
  }
}
```

**Error Responses:**
- `400`: Invalid OTP or expired
- `401`: Invalid token

---

## 🔗 Telegram Account Linking

For users who already have a web account and want to link it to Telegram.

### Flow Diagram

```
User logs in on web
       ↓
Request deep link (POST /api/mini-app/auth/connect-telegram/link/)
       ↓
Backend creates one-time UUID token
       ↓
Return deep link: t.me/Mazzalybot?start=<UUID>
       ↓
User clicks link → Opens Telegram bot
       ↓
Bot sends /start <UUID> to webhook
       ↓
Backend validates UUID and links account
       ↓
User can now use Mini App
```

### Request Deep Link

```javascript
async function getTelegramLinkURL() {
  const accessToken = localStorage.getItem('access_token');
  
  try {
    const response = await fetch('https://api.mazzaly.uz/api/mini-app/auth/connect-telegram/link/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': accessToken
      },
      body: JSON.stringify({})  // Empty body
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate link');
    }
    
    const data = await response.json();
    
    console.log('Telegram link:', data.deep_link);
    console.log('Expires in:', data.expires_in, 'seconds');
    
    return data;
  } catch (error) {
    console.error('Get link error:', error);
    throw error;
  }
}
```

**Endpoint:** `POST /api/mini-app/auth/connect-telegram/link/`

**Request:** `{}` (empty body)

**Success Response (200):**
```json
{
  "deep_link": "https://t.me/Mazzalybot?start=512442d5-8f2a-4e3b-9c1d-3a7b8c9d0e1f",
  "expires_in": 600,
  "expires_at": "2025-11-05T00:28:00Z"
}
```

**Error Responses:**
- `400`: Already linked to Telegram
- `401`: Invalid or missing token

### Display Link to User

```javascript
async function showTelegramLinkButton() {
  try {
    const data = await getTelegramLinkURL();
    
    // Option 1: Direct link (opens in browser)
    const linkHTML = `
      <a href="${data.deep_link}" target="_blank" class="btn btn-primary">
        Link Telegram Account
      </a>
      <p class="text-muted">Expires in ${Math.floor(data.expires_in / 60)} minutes</p>
    `;
    
    document.getElementById('telegram-link-container').innerHTML = linkHTML;
    
    // Option 2: Show QR code
    // generateQRCode(data.deep_link);
    
  } catch (error) {
    console.error('Error:', error);
  }
}
```

---

## 📚 API Reference

### Authentication

#### 1. Telegram Login
**POST** `/api/telegram-auth/`

- **Headers:** None required
- **Body:** `{ "init_data": "..." }`
- **Response:** JWT tokens + user info

#### 2. Token Refresh
**POST** `/api/token/refresh/`

- **Headers:** None
- **Body:** `{ "refresh": "..." }`
- **Response:** New access token

```javascript
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  const response = await fetch('https://api.mazzaly.uz/api/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  
  return data.access;
}
```

### Email Linking

#### 3. Send OTP
**POST** `/api/mini-app/auth/connect-email/`

- **Headers:** `Authorization: <access_token>`
- **Body:** `{ "email": "user@example.com" }`
- **Response:** Success message

#### 4. Verify OTP
**POST** `/api/mini-app/auth/OTP/`

- **Headers:** `Authorization: <access_token>`
- **Body:** `{ "email": "...", "otp": "123456" }`
- **Response:** Updated JWT tokens + user info

### Telegram Linking

#### 5. Get Deep Link
**POST** `/api/mini-app/auth/connect-telegram/link/`

- **Headers:** `Authorization: <access_token>`
- **Body:** `{}`
- **Response:** Deep link URL + expiry

---

## ⚠️ Error Handling

### Common HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Continue |
| 400 | Bad Request | Show error message to user |
| 401 | Unauthorized | Refresh token or re-login |
| 404 | Not Found | Check API endpoint |
| 500 | Server Error | Retry or contact support |

### Error Response Format

All errors return JSON:
```json
{
  "detail": "Error message here"
}
```

### Handle 401 Errors (Token Expired)

```javascript
async function fetchWithAuth(url, options = {}) {
  const accessToken = localStorage.getItem('access_token');
  
  // Add Authorization header
  options.headers = {
    ...options.headers,
    'Authorization': accessToken
  };
  
  let response = await fetch(url, options);
  
  // If 401, try to refresh token
  if (response.status === 401) {
    try {
      const newToken = await refreshToken();
      
      // Retry with new token
      options.headers['Authorization'] = newToken;
      response = await fetch(url, options);
    } catch (error) {
      // Refresh failed, re-login required
      console.error('Token refresh failed, please login again');
      // Redirect to login
      window.location.href = '/login';
    }
  }
  
  return response;
}
```

---

## 💡 Complete Examples

### Example 1: Mini App Initialization

```javascript
// app.js
class MazzalyMiniApp {
  constructor() {
    this.tg = window.Telegram.WebApp;
    this.baseURL = 'https://api.mazzaly.uz/api';
    this.init();
  }
  
  init() {
    // Expand app
    this.tg.expand();
    
    // Check if user is logged in
    const accessToken = localStorage.getItem('access_token');
    
    if (!accessToken) {
      // Not logged in, authenticate with Telegram
      this.loginWithTelegram();
    } else {
      // Already logged in, load user data
      this.loadUserData();
    }
    
    this.tg.ready();
  }
  
  async loginWithTelegram() {
    const initData = this.tg.initData;
    
    if (!initData) {
      console.error('No initData available');
      return;
    }
    
    try {
      const response = await fetch(`${this.baseURL}/telegram-auth/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ init_data: initData })
      });
      
      const data = await response.json();
      
      // Save tokens
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      // Show main app
      this.showMainApp(data.user);
      
    } catch (error) {
      console.error('Login failed:', error);
      this.showError('Authentication failed');
    }
  }
  
  showMainApp(user) {
    document.getElementById('app').innerHTML = `
      <h1>Welcome, ${user.first_name}!</h1>
      <p>Telegram ID: ${user.telegram_id}</p>
      <p>Login method: ${user.login_method}</p>
      
      ${!user.email ? `
        <button onclick="app.showEmailForm()">Link Email</button>
      ` : `
        <p>Email: ${user.email} ✓</p>
      `}
    `;
  }
  
  showEmailForm() {
    // Show email input form
  }
  
  async loadUserData() {
    // Fetch user profile
    const response = await this.fetchWithAuth(`${this.baseURL}/me/`);
    const user = await response.json();
    this.showMainApp(user);
  }
  
  async fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('access_token');
    options.headers = {
      ...options.headers,
      'Authorization': token
    };
    return fetch(url, options);
  }
  
  showError(message) {
    this.tg.showAlert(message);
  }
}

// Initialize app
const app = new MazzalyMiniApp();
```

### Example 2: Email Linking Component

```javascript
// email-linking.js
class EmailLinking {
  constructor(apiBaseURL) {
    this.apiBaseURL = apiBaseURL;
    this.step = 'input'; // 'input' | 'verify'
  }
  
  render() {
    const container = document.getElementById('email-container');
    
    if (this.step === 'input') {
      container.innerHTML = `
        <div class="email-form">
          <h3>Link Your Email</h3>
          <input type="email" id="email-input" placeholder="your@email.com" />
          <button onclick="emailLinking.sendOTP()">Send Code</button>
        </div>
      `;
    } else {
      container.innerHTML = `
        <div class="otp-form">
          <h3>Enter Verification Code</h3>
          <p>We sent a code to ${this.email}</p>
          <input type="text" id="otp-input" placeholder="123456" maxlength="6" />
          <button onclick="emailLinking.verifyOTP()">Verify</button>
          <button onclick="emailLinking.resendOTP()">Resend Code</button>
        </div>
      `;
    }
  }
  
  async sendOTP() {
    const email = document.getElementById('email-input').value;
    
    if (!this.validateEmail(email)) {
      alert('Please enter a valid email');
      return;
    }
    
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${this.apiBaseURL}/mini-app/auth/connect-email/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token
        },
        body: JSON.stringify({ email })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
      }
      
      this.email = email;
      this.step = 'verify';
      this.render();
      
    } catch (error) {
      alert('Error: ' + error.message);
    }
  }
  
  async verifyOTP() {
    const otp = document.getElementById('otp-input').value;
    
    if (otp.length !== 6) {
      alert('Please enter 6-digit code');
      return;
    }
    
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${this.apiBaseURL}/mini-app/auth/OTP/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token
        },
        body: JSON.stringify({
          email: this.email,
          otp: otp
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
      }
      
      const data = await response.json();
      
      // Update tokens
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      alert('Email linked successfully! ✓');
      
      // Reload app
      window.location.reload();
      
    } catch (error) {
      alert('Error: ' + error.message);
    }
  }
  
  async resendOTP() {
    await this.sendOTP();
  }
  
  validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
}

// Usage
const emailLinking = new EmailLinking('https://api.mazzaly.uz/api');
```

### Example 3: React/Vue Integration

```javascript
// React example
import { useState, useEffect } from 'react';

function MiniApp() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    
    loginWithTelegram();
  }, []);
  
  const loginWithTelegram = async () => {
    const tg = window.Telegram.WebApp;
    const initData = tg.initData;
    
    try {
      const response = await fetch('https://api.mazzaly.uz/api/telegram-auth/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ init_data: initData })
      });
      
      const data = await response.json();
      
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      
      setUser(data.user);
      setLoading(false);
      
    } catch (error) {
      console.error('Login error:', error);
      setLoading(false);
    }
  };
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  return (
    <div className="mini-app">
      <h1>Welcome, {user?.first_name}!</h1>
      {!user?.email && <EmailLinkingForm />}
    </div>
  );
}
```

---

## 🔧 Configuration

### Environment Variables (Frontend)

```javascript
// config.js
const config = {
  API_BASE_URL: 'https://api.mazzaly.uz/api',
  BOT_USERNAME: 'Mazzalybot',
  TELEGRAM_BOT_TOKEN: '2060951767:AAFcvGaYkm3N8fxp_4love7rrzIpueh5HkE',
  OTP_LENGTH: 6,
  OTP_EXPIRY_SECONDS: 300,
  LINK_EXPIRY_SECONDS: 600
};

export default config;
```

---

## 📱 Testing

### Test in Telegram

1. Open your bot: [@Mazzalybot](https://t.me/Mazzalybot)
2. Click "Menu" → Open Mini App
3. Your Mini App should load

### Test Locally

For local development, use ngrok or similar to expose your local server:

```bash
ngrok http 3000
```

Then update your bot's Mini App URL in BotFather.

### Debug Mode

```javascript
// Enable debug logging
const DEBUG = true;

function log(...args) {
  if (DEBUG) {
    console.log('[MiniApp]', ...args);
  }
}

// Usage
log('User logged in:', user);
log('Sending request to:', url);
```

---

## 🎨 UI/UX Best Practices

### 1. Show Loading States

```javascript
function showLoading(message = 'Loading...') {
  window.Telegram.WebApp.MainButton.text = message;
  window.Telegram.WebApp.MainButton.showProgress();
}

function hideLoading() {
  window.Telegram.WebApp.MainButton.hideProgress();
}
```

### 2. Use Telegram Theme Colors

```javascript
const tg = window.Telegram.WebApp;

// Apply theme colors
document.documentElement.style.setProperty('--bg-color', tg.backgroundColor);
document.documentElement.style.setProperty('--text-color', tg.themeParams.text_color);
document.documentElement.style.setProperty('--button-color', tg.themeParams.button_color);
```

### 3. Handle Back Button

```javascript
tg.BackButton.onClick(() => {
  // Handle back navigation
  goBack();
});

tg.BackButton.show();
```

---

## 📞 Support

For questions or issues:
- Backend API: Contact backend team
- Telegram Bot: [@Mazzalybot](https://t.me/Mazzalybot)
- Documentation: See `TELEGRAM_LINK_GUIDE.md` for backend details

---

## ✅ Checklist

- [ ] Telegram WebApp SDK included
- [ ] InitData sent to `/api/telegram-auth/`
- [ ] JWT tokens stored securely
- [ ] Authorization header added to requests
- [ ] Token refresh implemented
- [ ] Email linking tested
- [ ] Error handling implemented
- [ ] Loading states shown
- [ ] Telegram theme applied
- [ ] Tested in real Telegram app

---

**Last Updated:** November 5, 2025  
**API Version:** v1  
**Bot:** @Mazzalybot
