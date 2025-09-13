import os
import logging
import base64
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from data_manager import DataManager
from ai_services import AIServices

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Initialize data manager and AI services
data_manager = DataManager()
try:
    ai_services = AIServices()
except ValueError as e:
    logging.warning(f"AI services not available: {e}")
    ai_services = None

# Demo credentials for hackathon (in production, use proper user authentication)
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "password123"

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
        
        if username == DEMO_USERNAME and password == DEMO_PASSWORD:
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

@app.route('/leaderboard')
def leaderboard():
    """Farm leaderboard with geographic levels"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Get the level from query parameter, default to 'national'
    level = request.args.get('level', 'national')
    if level not in ['rural', 'district', 'state', 'national']:
        level = 'national'
    
    # Get leaderboard data for the selected level
    farms = data_manager.get_leaderboard_data(level)
    user_stats = data_manager.get_user_farm_stats()
    
    return render_template('leaderboard.html', 
                         farms=farms, 
                         level=level, 
                         user_stats=user_stats)

@app.route('/ai_chat')
def ai_chat():
    """AI Chat Assistant for farming guidance"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Get current farm info for context
    summary = data_manager.get_dashboard_summary()
    farm_info = {
        'capacity': summary.get('total_chickens', 150),
        'location': 'Rajkot, Gujarat',
        'health_status': data_manager.get_farm_health_status()
    }
    
    return render_template('ai_chat.html', farm_info=farm_info)

@app.route('/disease_detection')
def disease_detection():
    """AI Disease Detection through images and IoT sensors"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    return render_template('disease_detection.html')

@app.route('/api/ai_chat', methods=['POST'])
def api_ai_chat():
    """API endpoint for AI chat assistance"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not ai_services:
        return jsonify({
            'success': False,
            'advice': 'AI services are currently unavailable. Please check your API key configuration.'
        })
    
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'})
        
        # Get farm context
        summary = data_manager.get_dashboard_summary()
        context = f"Farm details: {summary['total_chickens']} birds, located in Gujarat, India"
        
        # Get AI advice
        result = ai_services.get_farming_advice(message, context)
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"AI chat error: {e}")
        return jsonify({
            'success': False,
            'advice': 'Sorry, I encountered an error. Please try again later.'
        })

@app.route('/api/analyze_disease_image', methods=['POST'])
def api_analyze_disease_image():
    """API endpoint for disease image analysis"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not ai_services:
        return jsonify({
            'success': False,
            'error': 'AI services are currently unavailable'
        })
    
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'})
        
        file = request.files['image']
        symptoms = request.form.get('symptoms', '')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Convert image to base64
        image_data = file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Analyze with AI
        result = ai_services.analyze_disease_image(image_base64, symptoms)
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Disease image analysis error: {e}")
        return jsonify({
            'success': False,
            'error': 'Image analysis failed. Please try again.'
        })

@app.route('/api/analyze_sensor_data', methods=['POST'])
def api_analyze_sensor_data():
    """API endpoint for IoT sensor data analysis"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not ai_services:
        return jsonify({
            'success': False,
            'error': 'AI services are currently unavailable'
        })
    
    try:
        sensor_data = request.get_json()
        
        # Analyze with AI
        result = ai_services.analyze_iot_sensor_data(sensor_data)
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Sensor data analysis error: {e}")
        return jsonify({
            'success': False,
            'error': 'Sensor data analysis failed. Please try again.'
        })

@app.route('/api/generate_prevention_plan', methods=['POST'])
def api_generate_prevention_plan():
    """API endpoint for generating disease prevention plan"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not ai_services:
        return jsonify({
            'success': False,
            'error': 'AI services are currently unavailable'
        })
    
    try:
        data = request.get_json()
        farm_size = data.get('farm_size', 150)
        season = data.get('season', 'current conditions')
        
        # Generate prevention plan with AI
        result = ai_services.get_disease_prevention_plan(farm_size, season)
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Prevention plan generation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Prevention plan generation failed. Please try again.'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
