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
    """Enhanced dashboard with farm score, tasks, and gamification"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Get today's summary data
    summary = data_manager.get_dashboard_summary()
    gamification = data_manager.get_gamification_data()
    tasks = data_manager.get_today_tasks()
    health_status = data_manager.get_farm_health_status()
    financial = data_manager.get_financial_summary()
    temp_alert = data_manager.check_temperature_alerts()
    
    return render_template('dashboard.html', 
                         summary=summary, 
                         gamification=gamification,
                         tasks=tasks,
                         health_status=health_status,
                         financial=financial,
                         temp_alert=temp_alert)

@app.route('/add_data', methods=['GET', 'POST'])
def add_data():
    """Add/Update daily farm data"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            date_str = request.form.get('date')
            if not date_str:
                raise ValueError("Date is required")
            
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

@app.route('/complete_task/<task_id>', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    success = data_manager.complete_task(task_id)
    if success:
        gamification = data_manager.get_gamification_data()
        flash(f'Task completed! +{[t["points"] for t in data_manager.get_today_tasks() if t["id"] == task_id][0]} points', 'success')
        return jsonify({'success': True, 'gamification': gamification})
    
    return jsonify({'success': False})

@app.route('/financial', methods=['GET', 'POST'])
def financial():
    """Revenue and expenses management"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            if not date_str:
                raise ValueError("Date is required")
            
            type_val = request.form.get('type')
            amount = float(request.form.get('amount', 0))
            description = request.form.get('description', '')
            
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            data_manager.add_revenue_expense(date_obj, type_val, amount, description)
            
            flash('Financial entry added successfully!', 'success')
            return redirect(url_for('financial'))
            
        except ValueError as e:
            flash('Invalid data format. Please check your inputs.', 'danger')
        except Exception as e:
            flash(f'Error adding entry: {str(e)}', 'danger')
    
    financial_data = data_manager.get_financial_summary()
    today = datetime.now().date()
    return render_template('financial.html', financial=financial_data, today=today)

@app.route('/diseases')
def diseases():
    """Disease solutions database"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('search', '')
    diseases = data_manager.search_diseases(query)
    
    return render_template('diseases.html', diseases=diseases, query=query)

@app.route('/training')
def training():
    """AI Training module with multilingual support"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    lang = request.args.get('lang', 'en')
    return render_template('training.html', lang=lang)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    """Business chat interface"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            data_manager.add_chat_message(session['username'], message, 'farmer')
            # Simulate supplier response
            import random
            responses = [
                'Thank you for your message. We\'ll get back to you soon.',
                'We have the feed you requested in stock.',
                'Our delivery truck can reach your farm tomorrow.',
                'Quality vaccines are available at discounted prices.'
            ]
            data_manager.add_chat_message('Supplier', random.choice(responses), 'supplier')
    
    messages = data_manager.get_chat_messages()
    return render_template('chat.html', messages=messages)

@app.route('/alerts')
def alerts():
    """Temperature and health alerts"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    alerts = data_manager.temperature_alerts
    return render_template('alerts.html', alerts=alerts)

@app.route('/visits')
def visits():
    """Farm visit tracking with QR code"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Generate QR code for farm visits
    farm_data = f"Farm Visit - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    qr_code = data_manager.generate_qr_code(farm_data)
    
    return render_template('visits.html', 
                         qr_code=qr_code, 
                         visit_count=data_manager.farm_visits)

@app.route('/add_visit', methods=['POST'])
def add_visit():
    """Add farm visit"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    count = data_manager.add_farm_visit()
    return jsonify({'success': True, 'count': count})

@app.route('/government_schemes')
def government_schemes():
    """Government schemes information"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    return render_template('government_schemes.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
