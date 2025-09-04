# Poultry Farm Management System

A comprehensive Flask-based web application for managing poultry farm operations with dashboard analytics, data entry, and reporting features. Built for Smart India Hackathon demonstration.

## Features

### 🔐 Authentication
- Admin login with session management
- Secure authentication flow
- Hardcoded demo credentials for easy testing

### 📊 Dashboard
- Real-time farm metrics overview
- Summary cards showing:
  - Total chickens
  - Daily egg production
  - Feed consumption
  - Profit/Loss calculations
- Quick action buttons for data entry

### 📝 Data Management
- Daily farm data entry form
- Input validation and error handling
- Data fields include:
  - Date
  - Number of chickens
  - Eggs produced
  - Feed consumed (kg)
  - Daily expenses

### 📈 Reports & Analytics
- Interactive Chart.js visualizations
- Weekly egg production line chart
- Weekly feed consumption bar chart
- Responsive chart design with dark theme

### 🛠️ Technology Stack Page
- Visual representation of tech stack
- Development methodology explanation
- Feature highlights and security information

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Charts**: Chart.js
- **Storage**: In-memory Python data structures
- **Icons**: Font Awesome
- **Styling**: Bootstrap with Replit dark theme

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Quick Start

1. **Clone or download the application files**

2. **Install dependencies**
   ```bash
   pip install flask
   ```

3. **Set environment variable (optional)**
   ```bash
   export SESSION_SECRET="your-secret-key-here"
   ```
   *Note: If not set, a default development key will be used*

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the application**
   - Open your browser and navigate to: `http://localhost:5000`
   - Login with demo credentials:
     - Username: `admin`
     - Password: `password123`

## Application Structure

