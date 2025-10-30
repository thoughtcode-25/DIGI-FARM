import os
import logging
import base64
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from data_manager import DataManager
from ai_services import AIServices
from translations import get_text, get_available_languages

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

@app.context_processor
def inject_translations():
    """Make translation functions available in all templates"""
    farm_name = None
    if session.get('farm_registered') and session.get('farm_data'):
        farm_name = session.get('farm_data', {}).get('name', 'Your Farm')
    
    return {
        'get_text': get_text,
        'lang': session.get('language', 'en'),
        'farm_name': farm_name
    }

def get_manual_farming_advice(question, farm_type='chickens'):
    """Provide manual farming advice when AI services are unavailable"""
    question_lower = question.lower() if question else ""
    
    if any(word in question_lower for word in ['disease', 'prevention', 'health', 'sick']):
        if farm_type == 'pigs':
            return """**Pig Farm Health Management:**
            - Check pigs daily for fever, loss of appetite, or respiratory issues
            - Maintain strict biosecurity to prevent African Swine Fever
            - Ensure proper ventilation in pig housing
            - Consult veterinarian for vaccination schedule
            - Keep detailed health records for all pigs"""
        elif farm_type == 'both':
            return """**Mixed Farm Health Management:**
            - Maintain separate areas for chickens and pigs
            - Check all animals daily for signs of illness
            - Implement cross-species biosecurity protocols  
            - Follow vaccination schedules for both species
            - Consult veterinarian for comprehensive health program"""
        else:  # chickens or other
            return """**Poultry Health Management:**
            - Check birds daily for lethargy or unusual behavior
            - Maintain clean water and feed systems
            - Implement biosecurity measures
            - Follow vaccination schedule for Newcastle Disease, Avian Influenza
            - Quarantine new birds for 2-3 weeks"""
    elif any(word in question_lower for word in ['feed', 'nutrition', 'diet']):
        if farm_type == 'pigs':
            return """**Pig Nutrition Guidelines:**
            - Provide age-appropriate pig feed with proper protein content
            - Ensure fresh water access 24/7
            - Monitor feed quality and storage conditions
            - Adjust feeding based on growth stage and weight
            - Supplement with minerals and vitamins as needed"""
        elif farm_type == 'both':
            return """**Mixed Farm Nutrition:**
            - Use species-specific feeds for chickens and pigs
            - Prevent cross-contamination between feeds
            - Ensure fresh water for all animals
            - Monitor feed consumption patterns
            - Store different feeds separately"""
        else:  # chickens or other
            return """**Poultry Nutrition Guidelines:**
            - Provide balanced poultry feed: starter, grower, layer
            - Ensure fresh water available 24/7
            - Store feed in dry, rodent-proof containers  
            - Monitor egg production as nutrition indicator
            - Supplement calcium for laying hens"""
    else:
        return """**General Farm Management Tips:**
        - Maintain detailed records of all farm activities
        - Follow local regulations and obtain necessary permits
        - Implement proper waste management systems
        - Plan for seasonal changes and weather conditions
        - Build relationships with local veterinarians and suppliers
        
        For specific advice, please consult with agricultural extension services or veterinary professionals in your area."""

@app.route('/')
def index():
    """Show landing page with government theme"""
    return render_template('landing.html')

@app.route('/portal')  
def portal():
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
            # Set default language if not already set
            if 'language' not in session:
                session['language'] = 'en'
            session['language_selected'] = True  # Skip language selection
            flash(get_text('login_successful', session.get('language', 'en')), 'success')
            # Redirect to landing page after successful login
            return redirect(url_for('index'))
        else:
            flash(get_text('invalid_credentials', session.get('language', 'en')), 'danger')
            # Redirect back to landing page with error
            return redirect(url_for('index') + '?error=invalid')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    lang = session.get('language', 'en')
    session.clear()
    flash(get_text('logout', lang), 'success')
    return redirect(url_for('index'))

@app.route('/language_select')
def language_select():
    """Language selection page shown after login"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Allow users to change language even if already selected
    languages = get_available_languages()
    current_lang = session.get('language', 'en')
    return render_template('language_select.html', languages=languages, current_lang=current_lang)

@app.route('/set_language', methods=['POST'])
def set_language():
    """Set user's language preference"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json() or {}
    lang = data.get('language', 'en')
    if lang in get_available_languages():
        session['language'] = lang
        session['language_selected'] = True
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid language'}), 400

@app.route('/dashboard')
def dashboard():
    """Enhanced dashboard with farm score, tasks, and gamification"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Redirect to language selection if not done
    if not session.get('language_selected'):
        return redirect(url_for('language_select'))
    
    # Check if farm is registered
    if not session.get('farm_registered'):
        flash('Please register your farm first to access the dashboard.', 'info')
        return redirect(url_for('register_farm'))
    
    lang = session.get('language', 'en')
    
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
                         temp_alert=temp_alert,
                         lang=lang,
                         get_text=get_text)

@app.route('/add_data', methods=['GET', 'POST'])
def add_data():
    """Add/Update daily farm data"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if not session.get('language_selected'):
        return redirect(url_for('language_select'))
    
    lang = session.get('language', 'en')
    farm_type = data_manager.get_user_farm_type(session)
    
    if request.method == 'POST':
        try:
            # Get form data
            date_str = request.form.get('date')
            if not date_str:
                raise ValueError("Date is required")
            
            # Validate date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Get data based on farm type
            chickens = 0
            eggs = 0
            pigs = 0
            pig_weight = 0.0
            chicken_feed = 0.0
            pig_feed = 0.0
            
            if farm_type in ['chickens', 'both']:
                chickens = int(request.form.get('chickens', 0))
                eggs = int(request.form.get('eggs', 0))
                chicken_feed = float(request.form.get('chicken_feed', 0))
            
            if farm_type in ['pigs', 'both']:
                pigs = int(request.form.get('pigs', 0))
                pig_weight = float(request.form.get('pig_weight', 0))
                pig_feed = float(request.form.get('pig_feed', 0))
            
            expenses = float(request.form.get('expenses', 0))
            
            # Add data
            if farm_type == 'chickens':
                data_manager.add_daily_data(date_obj, chickens, eggs, chicken_feed, expenses)
            elif farm_type == 'pigs':
                data_manager.add_daily_data(date_obj, pigs, 0, pig_feed, expenses)
            elif farm_type == 'both':
                total_feed = chicken_feed + pig_feed
                data_manager.add_daily_data(date_obj, chickens, eggs, total_feed, expenses)
            
            flash(get_text('data_added_successfully', lang), 'success')
            return redirect(url_for('dashboard'))
            
        except ValueError as e:
            flash(get_text('invalid_data', lang), 'danger')
        except Exception as e:
            flash(f"{get_text('error_adding_data', lang)}: {str(e)}", 'danger')
    
    # Get today's date for form default
    today = datetime.now().date()
    return render_template('add_data.html', today=today, lang=lang, get_text=get_text, farm_type=farm_type)

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
    
    if not session.get('language_selected'):
        return redirect(url_for('language_select'))
    
    lang = session.get('language', 'en')
    
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
            
            flash(get_text('data_added_successfully', lang), 'success')
            return redirect(url_for('financial'))
            
        except ValueError as e:
            flash(get_text('invalid_data', lang), 'danger')
        except Exception as e:
            flash(f'{get_text("error_adding_data", lang)}: {str(e)}', 'danger')
    
    financial_data = data_manager.get_financial_summary()
    today = datetime.now().date()
    return render_template('financial.html', financial=financial_data, today=today, lang=lang, get_text=get_text)

@app.route('/financial/edit/<int:entry_id>', methods=['GET', 'POST'])
def edit_financial_entry(entry_id):
    """Edit financial entry"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if not session.get('language_selected'):
        return redirect(url_for('language_select'))
    
    lang = session.get('language', 'en')
    
    entry = data_manager.get_revenue_expense_by_id(entry_id)
    if not entry:
        flash(get_text('error_adding_data', lang), 'danger')
        return redirect(url_for('financial'))
    
    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            if not date_str:
                raise ValueError("Date is required")
            
            type_val = request.form.get('type')
            amount = float(request.form.get('amount', 0))
            description = request.form.get('description', '')
            
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            if data_manager.edit_revenue_expense(entry_id, date_obj, type_val, amount, description):
                flash(get_text('data_added_successfully', lang), 'success')
            else:
                flash(get_text('error_adding_data', lang), 'danger')
            
            return redirect(url_for('financial'))
            
        except ValueError as e:
            flash(get_text('invalid_data', lang), 'danger')
        except Exception as e:
            flash(f'{get_text("error_adding_data", lang)}: {str(e)}', 'danger')
    
    return render_template('edit_financial.html', entry=entry, lang=lang, get_text=get_text)

@app.route('/financial/delete/<int:entry_id>', methods=['POST'])
def delete_financial_entry(entry_id):
    """Delete financial entry"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    lang = session.get('language', 'en')
    
    if data_manager.delete_revenue_expense(entry_id):
        flash(get_text('data_added_successfully', lang), 'success')
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': get_text('error_adding_data', lang)})

@app.route('/diseases')
def diseases():
    """Disease solutions database filtered by farm type"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('search', '')
    farm_type = data_manager.get_user_farm_type(session)
    diseases = data_manager.search_diseases(query, farm_type)
    
    return render_template('diseases.html', diseases=diseases, query=query, farm_type=farm_type)

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
    lang = session.get('language', 'en')
    return render_template('chat.html', messages=messages, lang=lang, get_text=get_text)

@app.route('/alerts')
def alerts():
    """Temperature and health alerts"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    alerts = data_manager.temperature_alerts
    lang = session.get('language', 'en')
    return render_template('alerts.html', alerts=alerts, lang=lang, get_text=get_text)

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
    """Government schemes information filtered by farm type"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    farm_type = data_manager.get_user_farm_type(session)
    schemes = data_manager.get_government_schemes(farm_type)
    
    return render_template('government_schemes.html', schemes=schemes, farm_type=farm_type)

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
    
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'})
        
        # Get farm type
        farm_type = data_manager.get_user_farm_type(session)
        
        if not ai_services:
            # Provide farm-type-specific fallback advice even when AI services are unavailable
            fallback_advice = get_manual_farming_advice(message, farm_type)
            return jsonify({
                'success': True,
                'advice': fallback_advice,
                'note': 'AI services are currently unavailable. This is general farming advice based on your farm type.'
            })
        
        # Get farm context
        summary = data_manager.get_dashboard_summary()
        
        # Create farm-type specific context
        if farm_type == 'pigs':
            context = f"Farm details: {summary['total_chickens']} pigs, located in Gujarat, India"
        elif farm_type == 'both':
            context = f"Farm details: Mixed farm with livestock, located in Gujarat, India"
        elif farm_type == 'other':
            context = f"Farm details: Livestock farm, located in Gujarat, India"
        else:  # chickens
            context = f"Farm details: {summary['total_chickens']} birds, located in Gujarat, India"
        
        # Get AI advice with farm type context
        result = ai_services.get_farming_advice(message, context, farm_type)
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

@app.route('/rollback')
def rollback():
    """Trigger rollback options"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # This will show rollback options to the user
    flash("Here you can view project checkpoints to restore previous versions.", 'info')
    return redirect(url_for('dashboard'))

@app.route('/add_data_form')
def add_data_form():
    """Alternative route for add data form"""
    return redirect(url_for('add_data'))

@app.route('/tech_stack')
def tech_stack():
    """Technology stack information page"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    lang = session.get('language', 'en')
    return render_template('tech_stack.html', lang=lang, get_text=get_text)

@app.route('/register_farm', methods=['GET', 'POST'])
def register_farm():
    """Register a new farm"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle farm registration form submission
        farm_name = request.form.get('farm_name')
        farm_location = request.form.get('farm_location')
        farm_size = request.form.get('farm_size')
        livestock_type = request.form.get('livestock_type')
        contact_number = request.form.get('contact_number')
        
        # Store farm registration in session (in production, save to database)
        session['farm_registered'] = True
        session['farm_data'] = {
            'name': farm_name,
            'location': farm_location,
            'size': farm_size,
            'livestock_type': livestock_type,
            'contact_number': contact_number,
            'registration_date': datetime.now().isoformat(),
            'biosecurity_score': 85  # Initial score
        }
        
        flash('Farm registered successfully! Welcome to your dashboard.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register_farm.html')

@app.route('/open_farm')
def open_farm():
    """Open farm dashboard if registered, otherwise redirect to registration"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Check if language selection is needed
    if not session.get('language_selected'):
        return redirect(url_for('language_select'))
    
    # Check if farm is already registered
    if session.get('farm_registered'):
        # Farm is registered, go directly to dashboard
        return redirect(url_for('dashboard'))
    else:
        # Farm not registered, redirect to registration with message
        flash('Please register your farm first to access the dashboard.', 'info')
        return redirect(url_for('register_farm'))

@app.route('/business_chat')
def business_chat():
    """Chat platform for companies and suppliers"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    lang = session.get('language', 'en')
    
    # Mock chat data for companies and suppliers
    chat_rooms = [
        {
            'id': 1,
            'name': 'Poultry Suppliers Hub',
            'type': 'supplier',
            'members': 45,
            'active': True,
            'last_message': 'Looking for 500 broiler chicks this week',
            'last_time': '2 minutes ago'
        },
        {
            'id': 2,
            'name': 'Pig Breeding Network',
            'type': 'supplier',
            'members': 32,
            'active': True,
            'last_message': 'Premium Yorkshire pigs available',
            'last_time': '15 minutes ago'
        },
        {
            'id': 3,
            'name': 'Feed & Nutrition Exchange',
            'type': 'supplier',
            'members': 78,
            'active': False,
            'last_message': 'Organic feed suppliers needed',
            'last_time': '1 hour ago'
        }
    ]
    
    return render_template('business_chat.html', chat_rooms=chat_rooms, lang=lang, get_text=get_text)

@app.route('/leaderboard_page')
def leaderboard_page():
    """Enhanced leaderboard with farm details and chat functionality"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    lang = session.get('language', 'en')
    
    # Mock leaderboard data with farm details
    leaderboard_farms = [
        {
            'rank': 1,
            'farm_name': 'Green Valley Poultry',
            'owner': 'Rajesh Kumar',
            'location': 'Punjab, India',
            'biosecurity_score': 95,
            'livestock': {'chickens': 2500, 'pigs': 150},
            'achievements': ['Top Producer 2024', 'Eco-Friendly'],
            'contact_available': True
        },
        {
            'rank': 2,
            'farm_name': 'Sunrise Livestock Farm',
            'owner': 'Priya Sharma',
            'location': 'Haryana, India',
            'biosecurity_score': 92,
            'livestock': {'chickens': 2200, 'pigs': 200},
            'achievements': ['Innovation Award', 'Sustainable Farming'],
            'contact_available': True
        },
        {
            'rank': 3,
            'farm_name': 'Golden Feather Farm',
            'owner': 'Amit Singh',
            'location': 'Uttar Pradesh, India',
            'biosecurity_score': 89,
            'livestock': {'chickens': 1800, 'pigs': 120},
            'achievements': ['Quality Excellence'],
            'contact_available': False
        },
        {
            'rank': 4,
            'farm_name': 'Rural Pride Poultry',
            'owner': 'Sunita Devi',
            'location': 'Bihar, India',
            'biosecurity_score': 87,
            'livestock': {'chickens': 1500, 'pigs': 80},
            'achievements': ['Community Leader'],
            'contact_available': True
        },
        {
            'rank': 5,
            'farm_name': 'Modern Agri Solutions',
            'owner': 'Vikram Patel',
            'location': 'Gujarat, India',
            'biosecurity_score': 85,
            'livestock': {'chickens': 1200, 'pigs': 100},
            'achievements': ['Tech Innovator'],
            'contact_available': True
        }
    ]
    
    # Add current user's farm if registered
    if session.get('farm_registered'):
        user_farm = {
            'rank': 6,
            'farm_name': session['farm_data']['name'],
            'owner': session['username'],
            'location': session['farm_data']['location'],
            'biosecurity_score': session['farm_data']['biosecurity_score'],
            'livestock': {'chickens': 800, 'pigs': 50},
            'achievements': ['New Farmer'],
            'contact_available': True,
            'is_current_user': True
        }
        leaderboard_farms.append(user_farm)
    
    return render_template('leaderboard_page.html', 
                         leaderboard_farms=leaderboard_farms, 
                         lang=lang, 
                         get_text=get_text)

@app.route('/farm_analytics')
def farm_analytics():
    """Farm analytics page"""
    return redirect(url_for('reports'))

@app.route('/visit_tracking')
def visit_tracking():
    """Visit tracking page"""
    return redirect(url_for('visits'))

@app.route('/financial_records')
def financial_records():
    """Financial records page - redirect to financial"""
    return redirect(url_for('financial'))

@app.route('/add_daily_data')
def add_daily_data():
    """Add daily data page - redirect to add_data"""
    return redirect(url_for('add_data'))

@app.route('/farm_tools')
def farm_tools():
    """Farm tools overview page"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    lang = session.get('language', 'en')
    
    # Show overview of all farm tools
    tools = [
        {
            'name': 'Disease Solutions',
            'description': 'Identify and treat common poultry diseases',
            'icon': 'fas fa-stethoscope',
            'url': url_for('diseases'),
            'color': 'primary'
        },
        {
            'name': 'Training Modules',
            'description': 'Learn modern farming techniques',
            'icon': 'fas fa-graduation-cap',
            'url': url_for('training'),
            'color': 'success'
        },
        {
            'name': 'Business Chat',
            'description': 'Connect with suppliers and buyers',
            'icon': 'fas fa-comments',
            'url': url_for('chat'),
            'color': 'info'
        },
        {
            'name': 'Visit Tracking',
            'description': 'Track farm visitors with QR codes',
            'icon': 'fas fa-qrcode',
            'url': url_for('visits'),
            'color': 'warning'
        }
    ]
    
    return render_template('farm_tools.html', tools=tools, lang=lang, get_text=get_text)

@app.route('/analytics')
def analytics():
    """Analytics overview page"""
    return redirect(url_for('reports'))

@app.route('/production_reports')
def production_reports():
    """Production reports page"""
    return redirect(url_for('reports'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
