import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from data_manager import DataManager

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-for-demo")

# Initialize data manager
data_manager = DataManager()

# Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

@app.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login"""
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page with hardcoded credentials"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard with summary cards"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Get today's summary data
    summary = data_manager.get_dashboard_summary()
    
    return render_template('dashboard.html', summary=summary)

@app.route('/add_data', methods=['GET', 'POST'])
def add_data():
    """Add/Update daily farm data"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            date_str = request.form.get('date')
            chickens = int(request.form.get('chickens', 0))
            eggs = int(request.form.get('eggs', 0))
            feed = float(request.form.get('feed', 0))
            expenses = float(request.form.get('expenses', 0))
            
            # Validate date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Add data
            data_manager.add_daily_data(date_obj, chickens, eggs, feed, expenses)
            flash('Data added successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except ValueError as e:
            flash('Invalid data format. Please check your inputs.', 'danger')
        except Exception as e:
            flash(f'Error adding data: {str(e)}', 'danger')
    
    # Get today's date for form default
    today = datetime.now().date()
    return render_template('add_data.html', today=today)

@app.route('/reports')
def reports():
    """Reports page with charts"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    return render_template('reports.html')

@app.route('/api/chart_data')
def chart_data():
    """API endpoint for chart data"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get last 7 days of data for charts
    chart_data = data_manager.get_chart_data()
    return jsonify(chart_data)

@app.route('/tech_stack')
def tech_stack():
    """Technology stack and methodology page"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    return render_template('tech_stack.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
