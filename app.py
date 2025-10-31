import os
import logging
import base64
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from app_init import app, db
from data_manager import DataManager
from ai_services import AIServices
from translations import get_text, get_available_languages
from sms_service import SMSService

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Initialize data manager, AI services, and SMS service
data_manager = DataManager()
try:
    ai_services = AIServices()
except ValueError as e:
    logging.warning(f"AI services not available: {e}")
    ai_services = None

sms_service = SMSService()

# Demo credentials for hackathon (in production, use proper user authentication)
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "password123"

def get_user_id():
    """Get current user ID from session (username for now)"""
    return session.get('username', 'admin')

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

def get_manual_farming_advice(question, farm_type='layer'):
    """Provide manual farming advice when AI services are unavailable"""
    question_lower = question.lower() if question else ""
    
    if any(word in question_lower for word in ['disease', 'prevention', 'health', 'sick']):
        return """**Poultry Health Management:**
        - Check birds daily for lethargy or unusual behavior
        - Maintain clean water and feed systems
        - Implement biosecurity measures
        - Follow vaccination schedule for Newcastle Disease, Avian Influenza
        - Quarantine new birds for 2-3 weeks
        - Monitor respiratory health and flock behavior
        - Keep detailed health records for all birds"""
    elif any(word in question_lower for word in ['feed', 'nutrition', 'diet']):
        if farm_type == 'broiler':
            return """**Broiler Nutrition Guidelines:**
            - Provide high-protein broiler feed (20-24% protein)
            - Ensure fresh water available 24/7
            - Store feed in dry, rodent-proof containers
            - Monitor feed conversion ratio for optimal growth
            - Follow starter, grower, and finisher feeding schedule"""
        elif farm_type == 'layer':
            return """**Layer Nutrition Guidelines:**
            - Provide balanced layer feed (14-16% protein)
            - Ensure fresh water available 24/7
            - Supplement calcium for strong eggshells
            - Monitor egg production as nutrition indicator
            - Store feed in dry, rodent-proof containers"""
        else:
            return """**Poultry Nutrition Guidelines:**
            - Provide balanced poultry feed: starter, grower, layer
            - Ensure fresh water available 24/7
            - Store feed in dry, rodent-proof containers  
            - Monitor growth and production indicators
            - Supplement with minerals and vitamins as needed"""
    else:
        return """**General Poultry Farm Management Tips:**
        - Maintain detailed records of all farm activities
        - Follow local regulations and obtain necessary permits
        - Implement proper waste management systems
        - Plan for seasonal changes and weather conditions
        - Build relationships with local veterinarians and suppliers
        - Ensure proper ventilation and housing conditions
        
        For specific advice, please consult with agricultural extension services or veterinary professionals in your area."""

@app.route('/')
def index():
    """Show landing page with government theme and live statistics"""
    current_datetime = datetime.now()
    
    # Get leaderboard farms data for aggregated statistics
    leaderboard_farms = data_manager.get_leaderboard_data('national')
    total_farms = len(leaderboard_farms)
    
    # Calculate aggregated statistics from leaderboard farms
    total_chickens = sum(farm.get('capacity', 0) for farm in leaderboard_farms)
    
    # Use aggregated statistics from leaderboard instead of user-specific data
    # For landing page, we show aggregate data from all farms
    weekly_eggs = 8500  # Estimated weekly production from all farms
    total_eggs = total_chickens * 250  # Estimated annual production
    
    stats = {
        'current_datetime': current_datetime,
        'total_chickens': total_chickens,
        'total_eggs': total_eggs,
        'total_farms': total_farms,
        'weekly_eggs': weekly_eggs,
        'current_year': current_datetime.year
    }
    
    return render_template('landing.html', stats=stats)

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
    user_id = get_user_id()
    
    # Get today's summary data
    summary = data_manager.get_dashboard_summary(user_id)
    gamification = data_manager.get_gamification_data(user_id)
    tasks = data_manager.get_today_tasks(user_id)
    health_status = data_manager.get_farm_health_status(user_id)
    financial = data_manager.get_financial_summary(user_id)
    temp_alert = data_manager.check_temperature_alerts(user_id)
    
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
            
            # Get chicken farm data
            chickens = int(request.form.get('chickens', 0))
            eggs = int(request.form.get('eggs', 0))
            chicken_feed = float(request.form.get('chicken_feed', 0))
            expenses = float(request.form.get('expenses', 0))
            
            # Add data for the current user
            user_id = get_user_id()
            data_manager.add_daily_data(user_id, date_obj, chickens, eggs, chicken_feed, expenses)
            
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
    
    user_id = get_user_id()
    # Get last 7 days of data for charts
    chart_data = data_manager.get_chart_data(user_id)
    return jsonify(chart_data)


@app.route('/complete_task/<task_id>', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = get_user_id()
    success = data_manager.complete_task(user_id, task_id)
    if success:
        gamification = data_manager.get_gamification_data(user_id)
        flash(f'Task completed! +{[t["points"] for t in data_manager.get_today_tasks(user_id) if t["id"] == task_id][0]} points', 'success')
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
            user_id = get_user_id()
            data_manager.add_revenue_expense(user_id, date_obj, type_val, amount, description)
            
            flash(get_text('data_added_successfully', lang), 'success')
            return redirect(url_for('financial'))
            
        except ValueError as e:
            flash(get_text('invalid_data', lang), 'danger')
        except Exception as e:
            flash(f'{get_text("error_adding_data", lang)}: {str(e)}', 'danger')
    
    user_id = get_user_id()
    financial_data = data_manager.get_financial_summary(user_id)
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
    user_id = get_user_id()
    
    entry = data_manager.get_revenue_expense_by_id(user_id, entry_id)
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
            
            if data_manager.edit_revenue_expense(user_id, entry_id, date_obj, type_val, amount, description):
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
    user_id = get_user_id()
    
    if data_manager.delete_revenue_expense(user_id, entry_id):
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
    
    user_id = get_user_id()
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            data_manager.add_chat_message(user_id, session['username'], message, 'farmer')
            # Simulate supplier response
            import random
            responses = [
                'Thank you for your message. We\'ll get back to you soon.',
                'We have the feed you requested in stock.',
                'Our delivery truck can reach your farm tomorrow.',
                'Quality vaccines are available at discounted prices.'
            ]
            data_manager.add_chat_message(user_id, 'Supplier', random.choice(responses), 'supplier')
    
    messages = data_manager.get_chat_messages(user_id)
    lang = session.get('language', 'en')
    return render_template('chat.html', messages=messages, lang=lang, get_text=get_text)

@app.route('/alerts')
def alerts():
    """Temperature and health alerts"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    user_id = get_user_id()
    data_manager.ensure_user_context(user_id)
    alerts = data_manager.user_data[user_id]['temperature_alerts']
    lang = session.get('language', 'en')
    return render_template('alerts.html', alerts=alerts, lang=lang, get_text=get_text)

@app.route('/visits')
def visits():
    """Farm visit tracking with QR code"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    user_id = get_user_id()
    data_manager.ensure_user_context(user_id)
    
    # Generate QR code for farm visits
    farm_data = f"Farm Visit - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    qr_code = data_manager.generate_qr_code(farm_data)
    
    return render_template('visits.html', 
                         qr_code=qr_code, 
                         visit_count=data_manager.user_data[user_id]['farm_visits'])

@app.route('/add_visit', methods=['POST'])
def add_visit():
    """Add farm visit"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = get_user_id()
    count = data_manager.add_farm_visit(user_id)
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
    
    user_id = get_user_id()
    # Get current farm info for context
    summary = data_manager.get_dashboard_summary(user_id)
    farm_info = {
        'capacity': summary.get('total_chickens', 0),
        'location': 'Rajkot, Gujarat',
        'health_status': data_manager.get_farm_health_status(user_id)
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
        user_id = get_user_id()
        
        if not ai_services:
            # Provide farm-type-specific fallback advice even when AI services are unavailable
            fallback_advice = get_manual_farming_advice(message, farm_type)
            return jsonify({
                'success': True,
                'advice': fallback_advice,
                'note': 'AI services are currently unavailable. This is general farming advice based on your farm type.'
            })
        
        # Get farm context
        summary = data_manager.get_dashboard_summary(user_id)
        
        # Create farm-type specific context
        farm_type_names = {
            'broiler': 'Broiler (Meat Production) Farm',
            'layer': 'Layer (Egg Production) Farm',
            'dual_purpose': 'Dual-Purpose Farm',
            'breeder': 'Breeder Farm',
            'backyard': 'Backyard/Free-Range Farm'
        }
        farm_type_name = farm_type_names.get(farm_type, 'Poultry Farm')
        context = f"Farm details: {farm_type_name} with {summary['total_chickens']} birds, located in Gujarat, India"
        
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
        action = request.form.get('action', 'register')
        
        if action == 'send_otp':
            # Register farm directly without OTP (SMS disabled)
            contact_number = request.form.get('contact_number')
            farm_name = request.form.get('farm_name')
            farm_location = request.form.get('farm_location')
            farm_size = request.form.get('farm_size')
            farm_type = request.form.get('farm_type')
            
            if not contact_number:
                flash('Please provide a contact number', 'danger')
                return redirect(url_for('register_farm'))
            
            # Complete registration directly (SMS verification disabled)
            session['farm_registered'] = True
            session['farm_data'] = {
                'name': farm_name,
                'location': farm_location,
                'size': farm_size,
                'farm_type': farm_type,
                'contact_number': contact_number,
                'registration_date': datetime.now().isoformat(),
                'biosecurity_score': 85,
                'verified': False  # Not verified via SMS
            }
            
            # Initialize user data in DataManager for new farm registration
            user_id = get_user_id()
            data_manager.ensure_user_context(user_id)
            
            flash('Farm registered successfully! (SMS verification unavailable)', 'success')
            return redirect(url_for('dashboard'))
        
        elif action == 'verify':
            # Verify OTP and complete registration
            otp = request.form.get('otp')
            contact_number = session.get('pending_registration', {}).get('contact_number')
            
            if not contact_number or not otp:
                flash('Invalid verification request', 'danger')
                return redirect(url_for('register_farm'))
            
            verified, msg = sms_service.verify_otp(contact_number, otp)
            
            if verified:
                # Complete registration
                pending = session.get('pending_registration')
                if not pending:
                    flash('Registration data not found. Please start registration again.', 'danger')
                    return redirect(url_for('register_farm'))
                
                session['farm_registered'] = True
                session['farm_data'] = {
                    'name': pending['farm_name'],
                    'location': pending['farm_location'],
                    'size': pending['farm_size'],
                    'farm_type': pending['farm_type'],
                    'contact_number': pending['contact_number'],
                    'registration_date': datetime.now().isoformat(),
                    'biosecurity_score': 85,
                    'verified': True
                }
                
                # Initialize user data in DataManager for new farm registration
                user_id = get_user_id()
                data_manager.ensure_user_context(user_id)
                
                # Clear pending registration
                session.pop('pending_registration', None)
                
                flash('Farm registered and verified successfully! Welcome to your dashboard.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash(f'Verification failed: {msg}', 'danger')
                return render_template('verify_otp.html', contact_number=contact_number, purpose='registration')
    
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
            'name': 'Layer Farm Equipment Exchange',
            'type': 'supplier',
            'members': 38,
            'active': True,
            'last_message': 'High-quality egg collection systems available',
            'last_time': '12 minutes ago'
        },
        {
            'id': 3,
            'name': 'Feed & Nutrition Exchange',
            'type': 'supplier',
            'members': 78,
            'active': False,
            'last_message': 'Organic poultry feed suppliers needed',
            'last_time': '1 hour ago'
        },
        {
            'id': 4,
            'name': 'Broiler Farmers Network',
            'type': 'community',
            'members': 52,
            'active': True,
            'last_message': 'Tips for improving feed conversion ratio',
            'last_time': '30 minutes ago'
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
            'livestock': {'chickens': 2500},
            'farm_type': 'layer',
            'achievements': ['Top Producer 2024', 'Eco-Friendly'],
            'contact_available': True
        },
        {
            'rank': 2,
            'farm_name': 'Sunrise Broiler Farm',
            'owner': 'Priya Sharma',
            'location': 'Haryana, India',
            'biosecurity_score': 92,
            'livestock': {'chickens': 3200},
            'farm_type': 'broiler',
            'achievements': ['Innovation Award', 'Sustainable Farming'],
            'contact_available': True
        },
        {
            'rank': 3,
            'farm_name': 'Golden Feather Farm',
            'owner': 'Amit Singh',
            'location': 'Uttar Pradesh, India',
            'biosecurity_score': 89,
            'livestock': {'chickens': 1800},
            'farm_type': 'dual_purpose',
            'achievements': ['Quality Excellence'],
            'contact_available': False
        },
        {
            'rank': 4,
            'farm_name': 'Rural Pride Poultry',
            'owner': 'Sunita Devi',
            'location': 'Bihar, India',
            'biosecurity_score': 87,
            'livestock': {'chickens': 1500},
            'farm_type': 'backyard',
            'achievements': ['Community Leader'],
            'contact_available': True
        },
        {
            'rank': 5,
            'farm_name': 'Modern Agri Solutions',
            'owner': 'Vikram Patel',
            'location': 'Gujarat, India',
            'biosecurity_score': 85,
            'livestock': {'chickens': 2200},
            'farm_type': 'layer',
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
            'livestock': {'chickens': 800},
            'farm_type': session['farm_data'].get('farm_type', 'layer'),
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

@app.route('/api/send_flu_alert', methods=['POST'])
def send_flu_alert_api():
    """API endpoint to send flu alert to farm owner"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        location = data.get('location', session.get('farm_data', {}).get('location', 'your area'))
        
        # Get farm data from session
        farm_data = session.get('farm_data', {})
        contact_number = farm_data.get('contact_number')
        farm_name = farm_data.get('name', 'Farm Owner')
        
        if not contact_number:
            return jsonify({
                'success': False,
                'error': 'No contact number registered'
            })
        
        # Send flu alert via SMS
        success, msg = sms_service.send_flu_alert(contact_number, location, farm_name)
        
        if success:
            logging.info(f"Flu alert sent successfully to {contact_number}")
            return jsonify({
                'success': True,
                'message': 'Flu alert sent successfully via SMS'
            })
        else:
            logging.error(f"Failed to send flu alert: {msg}")
            return jsonify({
                'success': False,
                'error': msg
            })
    
    except Exception as e:
        logging.error(f"Flu alert API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/send_disease_alert', methods=['POST'])
def send_disease_alert_api():
    """API endpoint to send disease alert to farm owner"""
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        disease_name = data.get('disease_name', 'Disease')
        location = data.get('location', session.get('farm_data', {}).get('location', 'your area'))
        
        # Get farm data from session
        farm_data = session.get('farm_data', {})
        contact_number = farm_data.get('contact_number')
        farm_name = farm_data.get('name', 'Farm Owner')
        farm_type = farm_data.get('farm_type', 'layer')
        
        if not contact_number:
            return jsonify({
                'success': False,
                'error': 'No contact number registered'
            })
        
        # Send disease alert via SMS
        success, msg = sms_service.send_disease_alert(contact_number, disease_name, location, farm_name, farm_type)
        
        if success:
            logging.info(f"Disease alert sent successfully to {contact_number}")
            return jsonify({
                'success': True,
                'message': f'{disease_name} alert sent successfully via SMS'
            })
        else:
            logging.error(f"Failed to send disease alert: {msg}")
            return jsonify({
                'success': False,
                'error': msg
            })
    
    except Exception as e:
        logging.error(f"Disease alert API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/farm-statistics/<farm_type>')
def get_farm_statistics(farm_type):
    """API endpoint to get real-time farm statistics from database"""
    try:
        from models import FarmStatistics
        
        stats = FarmStatistics.query.filter_by(farm_type=farm_type).first()
        
        if not stats:
            return jsonify({
                'success': False,
                'error': f'No statistics found for farm type: {farm_type}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': stats.to_dict()
        })
    
    except Exception as e:
        logging.error(f"Error fetching farm statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
