from datetime import datetime, timedelta
from collections import defaultdict
import qrcode
import io
import base64
import random

class DataManager:
    """Manages in-memory data storage for the enhanced poultry farm application"""
    
    def __init__(self):
        # User-scoped storage - each user has their own data
        self.user_data = {}  # user_id -> {daily_data, tasks, completed_tasks, points, level, badges, etc.}
        
        # Shared/global data (not user-specific)
        self.diseases_db = []
        self.government_schemes = []
        self.farms_data = []  # Leaderboard data
        
        # Initialize shared data
        self.initialize_diseases_db()
        self.initialize_government_schemes()
        self.initialize_farms_data()
    
    def ensure_user_context(self, user_id):
        """Ensure user data structure exists for a given user_id"""
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                'daily_data': {},  # date -> {chickens, eggs, feed, expenses}
                'tasks': {},  # date -> [task_id, ...]
                'completed_tasks': {},  # date -> [task_id, ...]
                'user_points': 0,
                'user_level': 1,
                'user_badges': [],
                'revenue_expenses': [],  # list of {date, type, amount, description}
                'chat_messages': [],
                'farm_visits': 0,
                'temperature_alerts': [],
                'farm_health_status': "good",  # good, warning, critical
            }
            # Initialize daily tasks for new user
            self.initialize_daily_tasks_for_user(user_id)
    
    def get_user_farm_type(self, session=None):
        """Get the user's registered farm type from session data"""
        if session and 'farm_data' in session:
            return session['farm_data'].get('farm_type', 'layer')
        return 'layer'  # Default fallback to layer farm
    
    
    def add_daily_data(self, user_id, date, chickens, eggs, feed, expenses):
        """Add or update daily farm data for a specific user"""
        self.ensure_user_context(user_id)
        self.user_data[user_id]['daily_data'][date] = {
            'chickens': chickens,
            'eggs': eggs,
            'feed': feed,
            'expenses': expenses
        }
    
    def get_dashboard_summary(self, user_id):
        """Get summary data for dashboard cards for a specific user"""
        self.ensure_user_context(user_id)
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Get user's daily data
        daily_data = self.user_data[user_id]['daily_data']
        
        # Get today's data or use latest available
        today_data = daily_data.get(today, daily_data.get(yesterday, {}))
        
        if not today_data:
            return {
                'total_chickens': 0,
                'eggs_today': 0,
                'feed_today': 0.0,
                'profit_loss': 0.0,
                'chickens_sold': 0
            }
        
        # Calculate profit/loss (assuming ₹5.00 per egg, ₹40.00 per kg feed)
        egg_price = 5.00
        feed_cost_per_kg = 40.00
        
        revenue = today_data.get('eggs', 0) * egg_price
        feed_cost = today_data.get('feed', 0) * feed_cost_per_kg
        total_expenses = today_data.get('expenses', 0) + feed_cost
        profit_loss = revenue - total_expenses
        
        return {
            'total_chickens': today_data.get('chickens', 0),
            'eggs_today': today_data.get('eggs', 0),
            'feed_today': today_data.get('feed', 0),
            'profit_loss': profit_loss,
            'chickens_sold': today_data.get('chickens_sold', 0)
        }
    
    def get_chart_data(self, user_id):
        """Get data formatted for Chart.js for a specific user"""
        self.ensure_user_context(user_id)
        
        # Get last 7 days of data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)
        
        # Get user's daily data
        daily_data = self.user_data[user_id]['daily_data']
        
        dates = []
        eggs_data = []
        feed_data = []
        
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%m/%d'))
            
            if current_date in daily_data:
                eggs_data.append(daily_data[current_date].get('eggs', 0))
                feed_data.append(daily_data[current_date].get('feed', 0))
            else:
                eggs_data.append(0)
                feed_data.append(0)
            
            current_date += timedelta(days=1)
        
        return {
            'labels': dates,
            'eggs': eggs_data,
            'feed': feed_data
        }
    
    def get_all_data(self, user_id):
        """Get all stored data for a specific user"""
        self.ensure_user_context(user_id)
        return dict(self.user_data[user_id]['daily_data'])
    
    def initialize_diseases_db(self):
        """Initialize diseases database for chicken poultry farming"""
        self.diseases_db = [
            # Chicken/Poultry diseases
            {
                'id': 1,
                'name': 'Newcastle Disease',
                'symptoms': 'Respiratory distress, nervous system disorders, egg production drop',
                'treatment': 'Vaccination, supportive care, isolation of affected birds',
                'prevention': 'Regular vaccination, biosecurity measures',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard']
            },
            {
                'id': 2,
                'name': 'Infectious Bronchitis',
                'symptoms': 'Coughing, sneezing, nasal discharge, reduced egg production',
                'treatment': 'Supportive care, antibiotics for secondary infections',
                'prevention': 'Vaccination, good ventilation, reduce stress',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard']
            },
            {
                'id': 3,
                'name': 'Avian Influenza',
                'symptoms': 'Sudden death, respiratory symptoms, drop in egg production',
                'treatment': 'No specific treatment, cull affected birds',
                'prevention': 'Biosecurity, avoid contact with wild birds',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard']
            },
            {
                'id': 4,
                'name': 'Coccidiosis',
                'symptoms': 'Bloody diarrhea, loss of appetite, weight loss',
                'treatment': 'Anticoccidial drugs, maintain dry environment',
                'prevention': 'Clean environment, proper feeding management',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard']
            },
            {
                'id': 5,
                'name': 'Marek\'s Disease',
                'symptoms': 'Paralysis, tumors, eye lesions',
                'treatment': 'No cure, supportive care',
                'prevention': 'Vaccination at day-old, good hygiene',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard']
            },
            {
                'id': 6,
                'name': 'Infectious Bursal Disease (Gumboro)',
                'symptoms': 'Depression, diarrhea, ruffled feathers, immunosuppression',
                'treatment': 'No specific treatment, supportive care',
                'prevention': 'Vaccination, proper hygiene, biosecurity',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard']
            },
            {
                'id': 7,
                'name': 'Fowl Pox',
                'symptoms': 'Wart-like lesions on skin, respiratory issues if diphtheritic form',
                'treatment': 'Supportive care, prevent secondary infections',
                'prevention': 'Vaccination, mosquito control',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard']
            },
            {
                'id': 8,
                'name': 'Egg Drop Syndrome',
                'symptoms': 'Sudden drop in egg production, soft-shelled or misshapen eggs',
                'treatment': 'No specific treatment, supportive care',
                'prevention': 'Vaccination, biosecurity measures',
                'farm_types': ['layer', 'dual_purpose', 'breeder']
            },
            {
                'id': 9,
                'name': 'Parasitic Infections',
                'symptoms': 'Weight loss, poor feather condition, reduced productivity',
                'treatment': 'Deworming drugs, improved hygiene',
                'prevention': 'Regular deworming, clean environment, proper sanitation',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard']
            },
            {
                'id': 10,
                'name': 'Nutritional Deficiencies',
                'symptoms': 'Poor growth, weakness, reduced egg production',
                'treatment': 'Balanced nutrition, vitamin/mineral supplements',
                'prevention': 'Quality feed, proper storage, regular feeding',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard']
            }
        ]
    
    def initialize_government_schemes(self):
        """Initialize government schemes data for chicken poultry farming"""
        self.government_schemes = [
            # Chicken/Poultry schemes
            {
                'id': 1,
                'name': 'Poultry Venture Capital Fund (PVCF)',
                'description': 'Financial assistance for setting up commercial poultry farms and hatcheries',
                'benefits': 'Up to ₹25 lakhs subsidy for poultry farming infrastructure',
                'eligibility': 'Farmers, cooperatives, and private companies',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard'],
                'category': 'Financial Assistance'
            },
            {
                'id': 2,
                'name': 'National Livestock Mission - Poultry Development',
                'description': 'Support for indigenous poultry breeds and backyard poultry development',
                'benefits': 'Subsidy on poultry equipment, training, and technical support',
                'eligibility': 'Small and marginal farmers, SHGs, rural entrepreneurs',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard'],
                'category': 'Development Program'
            },
            {
                'id': 3,
                'name': 'Poultry Insurance Scheme',
                'description': 'Insurance coverage for poultry against death due to diseases',
                'benefits': 'Premium subsidy up to 50% for insurance coverage',
                'eligibility': 'All poultry farmers',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard'],
                'category': 'Insurance'
            },
            {
                'id': 4,
                'name': 'Kisan Credit Card (Poultry)',
                'description': 'Credit facility for poultry farming activities',
                'benefits': 'Low-interest credit up to ₹3 lakhs without collateral',
                'eligibility': 'Farmers involved in poultry farming',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard'],
                'category': 'Credit & Finance'
            },
            {
                'id': 5,
                'name': 'MUDRA Loan for Poultry',
                'description': 'Micro-finance support for small poultry enterprises',
                'benefits': 'Loans up to ₹10 lakhs for poultry business',
                'eligibility': 'Micro-entrepreneurs in poultry sector',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard'],
                'category': 'Micro-Finance'
            },
            {
                'id': 6,
                'name': 'Backyard Poultry Development Scheme',
                'description': 'Support for backyard poultry farming in rural areas',
                'benefits': 'Free chicks, training, and vaccination support',
                'eligibility': 'Rural households, especially women SHGs',
                'farm_types': ['backyard'],
                'category': 'Rural Development'
            },
            {
                'id': 7,
                'name': 'Poultry Disease Control Programme',
                'description': 'Free vaccination and disease control measures for poultry farms',
                'benefits': 'Free vaccines, veterinary services, and emergency support',
                'eligibility': 'All registered poultry farmers',
                'farm_types': ['broiler', 'layer', 'dual_purpose', 'breeder', 'backyard'],
                'category': 'Health & Veterinary'
            },
            {
                'id': 8,
                'name': 'Broiler Production Subsidy',
                'description': 'Financial support for commercial broiler production units',
                'benefits': 'Subsidy on equipment and infrastructure for broiler farms',
                'eligibility': 'Commercial broiler farmers',
                'farm_types': ['broiler'],
                'category': 'Commercial Support'
            },
            {
                'id': 9,
                'name': 'Layer Farm Modernization Scheme',
                'description': 'Support for upgrading layer farms with modern equipment',
                'benefits': 'Subsidy on cage systems, egg collection, and storage equipment',
                'eligibility': 'Layer farm owners',
                'farm_types': ['layer'],
                'category': 'Modernization'
            }
        ]
    
    def get_government_schemes(self, farm_type=None):
        """Get government schemes filtered by farm type"""
        if not farm_type:
            return self.government_schemes
        
        return [
            scheme for scheme in self.government_schemes
            if farm_type in scheme.get('farm_types', [])
        ]
    
    def initialize_daily_tasks_for_user(self, user_id):
        """Initialize daily biosecurity tasks for a specific user"""
        if user_id not in self.user_data:
            return
            
        today = datetime.now().date()
        daily_tasks = [
            {'id': 'clean_feeders', 'name': 'Clean Feed and Water Systems', 'points': 10},
            {'id': 'check_health', 'name': 'Check Bird Health', 'points': 15},
            {'id': 'sanitize_entrance', 'name': 'Sanitize Farm Entrance', 'points': 10},
            {'id': 'record_temperature', 'name': 'Record Temperature', 'points': 5},
            {'id': 'collect_eggs', 'name': 'Collect and Store Eggs Properly', 'points': 10},
            {'id': 'check_fencing', 'name': 'Check Perimeter Fencing', 'points': 5}
        ]
        
        self.user_data[user_id]['tasks'][today] = daily_tasks
        self.user_data[user_id]['completed_tasks'][today] = []
    
    def complete_task(self, user_id, task_id):
        """Mark a task as completed and award points for a specific user"""
        self.ensure_user_context(user_id)
        today = datetime.now().date()
        
        user = self.user_data[user_id]
        if today not in user['tasks']:
            return False
            
        for task in user['tasks'][today]:
            if task['id'] == task_id and task_id not in user['completed_tasks'].get(today, []):
                user['completed_tasks'][today].append(task_id)
                user['user_points'] += task['points']
                
                # Check for level up
                if user['user_points'] >= 100 * user['user_level']:
                    user['user_level'] += 1
                    user['user_badges'].append(f'Level {user["user_level"]} Master')
                
                return True
        return False
    
    def get_gamification_data(self, user_id):
        """Get user progress and gamification data for a specific user"""
        self.ensure_user_context(user_id)
        today = datetime.now().date()
        
        user = self.user_data[user_id]
        total_tasks = len(user['tasks'].get(today, []))
        completed_tasks = len(user['completed_tasks'].get(today, []))
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'points': user['user_points'],
            'level': user['user_level'],
            'badges': user['user_badges'],
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': completion_rate,
            'next_level_points': 100 * user['user_level']
        }
    
    def get_today_tasks(self, user_id):
        """Get today's tasks with completion status for a specific user"""
        self.ensure_user_context(user_id)
        today = datetime.now().date()
        
        user = self.user_data[user_id]
        tasks = user['tasks'].get(today, [])
        completed = user['completed_tasks'].get(today, [])
        
        for task in tasks:
            task['completed'] = task['id'] in completed
        
        return tasks
    
    def add_revenue_expense(self, user_id, date, type_val, amount, description):
        """Add revenue or expense entry for a specific user"""
        self.ensure_user_context(user_id)
        self.user_data[user_id]['revenue_expenses'].append({
            'date': date,
            'type': type_val,
            'amount': float(amount),
            'description': description
        })
    
    def get_financial_summary(self, user_id):
        """Get financial summary with profit/loss calculation for a specific user"""
        self.ensure_user_context(user_id)
        revenue_expenses = self.user_data[user_id]['revenue_expenses']
        
        total_revenue = sum(item['amount'] for item in revenue_expenses if item['type'] == 'revenue')
        total_expenses = sum(item['amount'] for item in revenue_expenses if item['type'] == 'expense')
        profit_loss = total_revenue - total_expenses
        
        # Add IDs to entries if not present
        for i, entry in enumerate(revenue_expenses):
            if 'id' not in entry:
                entry['id'] = i + 1
        
        return {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'profit_loss': profit_loss,
            'recent_entries': sorted(revenue_expenses, key=lambda x: x['date'], reverse=True)[:10],
            'all_entries': sorted(revenue_expenses, key=lambda x: x['date'], reverse=True)
        }
    
    def edit_revenue_expense(self, user_id, entry_id, date, type_val, amount, description):
        """Edit an existing revenue or expense entry for a specific user"""
        self.ensure_user_context(user_id)
        for entry in self.user_data[user_id]['revenue_expenses']:
            if entry.get('id') == int(entry_id):
                entry['date'] = date
                entry['type'] = type_val
                entry['amount'] = float(amount)
                entry['description'] = description
                return True
        return False
    
    def delete_revenue_expense(self, user_id, entry_id):
        """Delete a revenue or expense entry for a specific user"""
        self.ensure_user_context(user_id)
        for i, entry in enumerate(self.user_data[user_id]['revenue_expenses']):
            if entry.get('id') == int(entry_id):
                self.user_data[user_id]['revenue_expenses'].pop(i)
                return True
        return False
    
    def get_revenue_expense_by_id(self, user_id, entry_id):
        """Get a specific revenue/expense entry by ID for a specific user"""
        self.ensure_user_context(user_id)
        for entry in self.user_data[user_id]['revenue_expenses']:
            if entry.get('id') == int(entry_id):
                return entry
        return None
    
    def search_diseases(self, query, farm_type=None):
        """Search diseases database filtered by farm type"""
        # Filter diseases by farm type first
        diseases_to_search = self.diseases_db
        if farm_type:
            diseases_to_search = [
                disease for disease in self.diseases_db
                if farm_type in disease.get('farm_types', [])
            ]
        
        if not query:
            return diseases_to_search
        
        query = query.lower()
        results = []
        for disease in diseases_to_search:
            if (query in disease['name'].lower() or 
                query in disease['symptoms'].lower() or 
                query in disease['treatment'].lower()):
                results.append(disease)
        
        return results
    
    def get_farm_health_status(self, user_id):
        """Get current farm health status for a specific user"""
        self.ensure_user_context(user_id)
        today = datetime.now().date()
        
        user = self.user_data[user_id]
        completed = len(user['completed_tasks'].get(today, []))
        total = len(user['tasks'].get(today, []))
        
        if total == 0:
            return 'warning'
        
        completion_rate = completed / total
        if completion_rate >= 0.8:
            return 'good'
        elif completion_rate >= 0.5:
            return 'warning'
        else:
            return 'critical'
    
    def generate_qr_code(self, data):
        """Generate QR code for farm visits"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def add_farm_visit(self, user_id):
        """Increment farm visit counter for a specific user"""
        self.ensure_user_context(user_id)
        self.user_data[user_id]['farm_visits'] += 1
        return self.user_data[user_id]['farm_visits']
    
    def add_chat_message(self, user_id, sender, message, sender_type='farmer'):
        """Add message to chat for a specific user"""
        self.ensure_user_context(user_id)
        self.user_data[user_id]['chat_messages'].append({
            'timestamp': datetime.now(),
            'sender': sender,
            'message': message,
            'sender_type': sender_type
        })
    
    def get_chat_messages(self, user_id):
        """Get chat messages for a specific user"""
        self.ensure_user_context(user_id)
        return self.user_data[user_id]['chat_messages']
    
    def check_temperature_alerts(self, user_id):
        """Check for temperature alerts (simulated) for a specific user"""
        self.ensure_user_context(user_id)
        import random
        
        # Simulate temperature reading
        current_temp = random.uniform(20, 35)
        if current_temp > 30 or current_temp < 22:
            alert = {
                'timestamp': datetime.now(),
                'temperature': current_temp,
                'status': 'warning' if 28 <= current_temp <= 32 else 'critical',
                'message': f'Temperature alert: {current_temp:.1f}°C detected'
            }
            self.user_data[user_id]['temperature_alerts'].append(alert)
            return alert
        return None
    
    def initialize_farms_data(self):
        """Initialize farms data for leaderboard"""
        # Indian states and districts sample data
        self.farms_data = [
            # Current user's farm
            {
                'id': 'user_farm',
                'name': 'Your Farm',
                'farmer_name': 'Admin',
                'village': 'Rajkot Village',
                'district': 'Rajkot',
                'state': 'Gujarat',
                'capacity': 150,
                'cleanliness_score': 85,
                'biosecurity_score': 90,
                'production_efficiency': 88,
                'total_score': 0,  # Will be calculated
                'is_user_farm': True
            },
            # Gujarat farms (same state)
            {
                'id': 'farm_001',
                'name': 'Sunrise Poultry Farm',
                'farmer_name': 'Ramesh Patel',
                'village': 'Anand Village',
                'district': 'Anand',
                'state': 'Gujarat',
                'capacity': 200,
                'cleanliness_score': 92,
                'biosecurity_score': 85,
                'production_efficiency': 90,
                'total_score': 0
            },
            {
                'id': 'farm_002',
                'name': 'Green Valley Poultry',
                'farmer_name': 'Kiran Shah',
                'village': 'Vadodara Rural',
                'district': 'Vadodara',
                'state': 'Gujarat',
                'capacity': 300,
                'cleanliness_score': 88,
                'biosecurity_score': 95,
                'production_efficiency': 85,
                'total_score': 0
            },
            # Same district farms
            {
                'id': 'farm_003',
                'name': 'Modern Poultry Center',
                'farmer_name': 'Dipak Joshi',
                'village': 'Rajkot City',
                'district': 'Rajkot',
                'state': 'Gujarat',
                'capacity': 180,
                'cleanliness_score': 90,
                'biosecurity_score': 88,
                'production_efficiency': 92,
                'total_score': 0
            },
            # Different states
            {
                'id': 'farm_004',
                'name': 'Punjab Poultry Excellence',
                'farmer_name': 'Harpreet Singh',
                'village': 'Ludhiana Rural',
                'district': 'Ludhiana',
                'state': 'Punjab',
                'capacity': 500,
                'cleanliness_score': 95,
                'biosecurity_score': 92,
                'production_efficiency': 94,
                'total_score': 0
            },
            {
                'id': 'farm_005',
                'name': 'Maharashtra Gold Farm',
                'farmer_name': 'Suresh Patil',
                'village': 'Pune Rural',
                'district': 'Pune',
                'state': 'Maharashtra',
                'capacity': 400,
                'cleanliness_score': 89,
                'biosecurity_score': 90,
                'production_efficiency': 91,
                'total_score': 0
            },
            {
                'id': 'farm_006',
                'name': 'Haryana Prime Poultry',
                'farmer_name': 'Rajesh Kumar',
                'village': 'Karnal Village',
                'district': 'Karnal',
                'state': 'Haryana',
                'capacity': 350,
                'cleanliness_score': 87,
                'biosecurity_score': 89,
                'production_efficiency': 88,
                'total_score': 0
            },
            {
                'id': 'farm_007',
                'name': 'Tamil Nadu Organic Farm',
                'farmer_name': 'Murugan Raj',
                'village': 'Coimbatore Rural',
                'district': 'Coimbatore',
                'state': 'Tamil Nadu',
                'capacity': 250,
                'cleanliness_score': 93,
                'biosecurity_score': 91,
                'production_efficiency': 89,
                'total_score': 0
            },
            {
                'id': 'farm_008',
                'name': 'Andhra Model Farm',
                'farmer_name': 'Venkat Reddy',
                'village': 'Vijayawada Rural',
                'district': 'Krishna',
                'state': 'Andhra Pradesh',
                'capacity': 280,
                'cleanliness_score': 86,
                'biosecurity_score': 94,
                'production_efficiency': 87,
                'total_score': 0
            },
            {
                'id': 'farm_009',
                'name': 'Uttar Pradesh Champion',
                'farmer_name': 'Amit Sharma',
                'village': 'Agra Rural',
                'district': 'Agra',
                'state': 'Uttar Pradesh',
                'capacity': 320,
                'cleanliness_score': 84,
                'biosecurity_score': 86,
                'production_efficiency': 90,
                'total_score': 0
            },
            {
                'id': 'farm_010',
                'name': 'West Bengal Excellence',
                'farmer_name': 'Subhas Das',
                'village': 'Kolkata Rural',
                'district': 'North 24 Parganas',
                'state': 'West Bengal',
                'capacity': 220,
                'cleanliness_score': 91,
                'biosecurity_score': 88,
                'production_efficiency': 85,
                'total_score': 0
            }
        ]
        
        # Calculate total scores for all farms
        for farm in self.farms_data:
            self.calculate_farm_score(farm)
    
    def calculate_farm_score(self, farm):
        """Calculate total score based on different factors"""
        # Weighted scoring system
        cleanliness_weight = 0.3
        biosecurity_weight = 0.4
        efficiency_weight = 0.3
        
        # Base score calculation
        base_score = (
            farm['cleanliness_score'] * cleanliness_weight +
            farm['biosecurity_score'] * biosecurity_weight +
            farm['production_efficiency'] * efficiency_weight
        )
        
        # Capacity bonus (larger farms get slight bonus)
        capacity_bonus = min(farm['capacity'] / 1000 * 5, 10)  # Max 10 bonus points
        
        farm['total_score'] = round(base_score + capacity_bonus, 1)
        return farm['total_score']
    
    def get_leaderboard_data(self, level='national'):
        """Get leaderboard data filtered by geographic level"""
        user_farm = next((f for f in self.farms_data if f.get('is_user_farm')), None)
        
        if level == 'rural' and user_farm:
            # Same village
            filtered_farms = [f for f in self.farms_data if f['village'] == user_farm['village']]
        elif level == 'district' and user_farm:
            # Same district
            filtered_farms = [f for f in self.farms_data if f['district'] == user_farm['district']]
        elif level == 'state' and user_farm:
            # Same state
            filtered_farms = [f for f in self.farms_data if f['state'] == user_farm['state']]
        else:
            # National level - all farms
            filtered_farms = self.farms_data
        
        # Sort by total score (descending)
        sorted_farms = sorted(filtered_farms, key=lambda x: x['total_score'], reverse=True)
        
        # Add rank
        for i, farm in enumerate(sorted_farms, 1):
            farm['rank'] = i
        
        return sorted_farms
    
    def get_user_farm_stats(self):
        """Get current user's farm statistics across all levels"""
        user_farm = next((f for f in self.farms_data if f.get('is_user_farm')), None)
        if not user_farm:
            return None
        
        stats = {
            'rural': {'rank': 0, 'total': 0},
            'district': {'rank': 0, 'total': 0},
            'state': {'rank': 0, 'total': 0},
            'national': {'rank': 0, 'total': 0}
        }
        
        for level in stats.keys():
            leaderboard = self.get_leaderboard_data(level)
            user_entry = next((f for f in leaderboard if f.get('is_user_farm')), None)
            if user_entry:
                stats[level]['rank'] = user_entry['rank']
                stats[level]['total'] = len(leaderboard)
        
        return stats
