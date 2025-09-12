from datetime import datetime, timedelta
from collections import defaultdict
import qrcode
import io
import base64
import random

class DataManager:
    """Manages in-memory data storage for the enhanced poultry farm application"""
    
    def __init__(self):
        # In-memory storage using dictionaries and lists
        self.daily_data = {}  # date -> {chickens, eggs, feed, expenses}
        self.tasks = {}  # date -> [task_id, ...]
        self.completed_tasks = {}  # date -> [task_id, ...]
        self.user_points = 0
        self.user_level = 1
        self.user_badges = []
        self.revenue_expenses = []  # list of {date, type, amount, description}
        self.diseases_db = []
        self.chat_messages = []
        self.farm_visits = 0
        self.temperature_alerts = []
        self.farm_health_status = "good"  # good, warning, critical
        self.initialize_sample_data()
        self.initialize_diseases_db()
        self.initialize_daily_tasks()
        self.initialize_farms_data()
    
    def initialize_sample_data(self):
        """Initialize with some sample data for demonstration"""
        # Add data for the last 7 days
        base_date = datetime.now().date()
        
        sample_data = [
            {'chickens': 150, 'eggs': 120, 'feed': 25.5, 'expenses': 150.0},
            {'chickens': 148, 'eggs': 115, 'feed': 24.8, 'expenses': 140.0},
            {'chickens': 152, 'eggs': 125, 'feed': 26.2, 'expenses': 160.0},
            {'chickens': 151, 'eggs': 118, 'feed': 25.0, 'expenses': 145.0},
            {'chickens': 149, 'eggs': 122, 'feed': 24.5, 'expenses': 155.0},
            {'chickens': 153, 'eggs': 128, 'feed': 26.8, 'expenses': 170.0},
            {'chickens': 150, 'eggs': 130, 'feed': 25.2, 'expenses': 165.0},
        ]
        
        for i, data in enumerate(sample_data):
            date = base_date - timedelta(days=6-i)
            self.daily_data[date] = data
    
    def add_daily_data(self, date, chickens, eggs, feed, expenses):
        """Add or update daily farm data"""
        self.daily_data[date] = {
            'chickens': chickens,
            'eggs': eggs,
            'feed': feed,
            'expenses': expenses
        }
    
    def get_dashboard_summary(self):
        """Get summary data for dashboard cards"""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Get today's data or use latest available
        today_data = self.daily_data.get(today, self.daily_data.get(yesterday, {}))
        
        if not today_data:
            return {
                'total_chickens': 0,
                'eggs_today': 0,
                'feed_today': 0.0,
                'profit_loss': 0.0
            }
        
        # Calculate profit/loss (assuming $0.50 per egg, $2.00 per kg feed)
        egg_price = 0.50
        feed_cost_per_kg = 2.00
        
        revenue = today_data.get('eggs', 0) * egg_price
        feed_cost = today_data.get('feed', 0) * feed_cost_per_kg
        total_expenses = today_data.get('expenses', 0) + feed_cost
        profit_loss = revenue - total_expenses
        
        return {
            'total_chickens': today_data.get('chickens', 0),
            'eggs_today': today_data.get('eggs', 0),
            'feed_today': today_data.get('feed', 0),
            'profit_loss': profit_loss
        }
    
    def get_chart_data(self):
        """Get data formatted for Chart.js"""
        # Get last 7 days of data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)
        
        dates = []
        eggs_data = []
        feed_data = []
        
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%m/%d'))
            
            if current_date in self.daily_data:
                eggs_data.append(self.daily_data[current_date].get('eggs', 0))
                feed_data.append(self.daily_data[current_date].get('feed', 0))
            else:
                eggs_data.append(0)
                feed_data.append(0)
            
            current_date += timedelta(days=1)
        
        return {
            'labels': dates,
            'eggs': eggs_data,
            'feed': feed_data
        }
    
    def get_all_data(self):
        """Get all stored data"""
        return dict(self.daily_data)
    
    def initialize_diseases_db(self):
        """Initialize diseases database with common poultry diseases"""
        self.diseases_db = [
            {
                'id': 1,
                'name': 'Newcastle Disease',
                'symptoms': 'Respiratory distress, nervous system disorders, egg production drop',
                'treatment': 'Vaccination, supportive care, isolation of affected birds',
                'prevention': 'Regular vaccination, biosecurity measures'
            },
            {
                'id': 2,
                'name': 'Infectious Bronchitis',
                'symptoms': 'Coughing, sneezing, nasal discharge, reduced egg production',
                'treatment': 'Supportive care, antibiotics for secondary infections',
                'prevention': 'Vaccination, good ventilation, reduce stress'
            },
            {
                'id': 3,
                'name': 'Avian Influenza',
                'symptoms': 'Sudden death, respiratory symptoms, drop in egg production',
                'treatment': 'No specific treatment, cull affected birds',
                'prevention': 'Biosecurity, avoid contact with wild birds'
            },
            {
                'id': 4,
                'name': 'Coccidiosis',
                'symptoms': 'Bloody diarrhea, loss of appetite, weight loss',
                'treatment': 'Anticoccidial drugs, maintain dry environment',
                'prevention': 'Clean environment, proper feeding management'
            },
            {
                'id': 5,
                'name': 'Marek\'s Disease',
                'symptoms': 'Paralysis, tumors, eye lesions',
                'treatment': 'No cure, supportive care',
                'prevention': 'Vaccination at day-old, good hygiene'
            }
        ]
    
    def initialize_daily_tasks(self):
        """Initialize daily biosecurity tasks"""
        today = datetime.now().date()
        daily_tasks = [
            {'id': 'clean_feeders', 'name': 'Clean Feed and Water Systems', 'points': 10},
            {'id': 'check_health', 'name': 'Check Bird Health', 'points': 15},
            {'id': 'sanitize_entrance', 'name': 'Sanitize Farm Entrance', 'points': 10},
            {'id': 'record_temperature', 'name': 'Record Temperature', 'points': 5},
            {'id': 'collect_eggs', 'name': 'Collect and Store Eggs Properly', 'points': 10},
            {'id': 'check_fencing', 'name': 'Check Perimeter Fencing', 'points': 5}
        ]
        
        self.tasks[today] = daily_tasks
        self.completed_tasks[today] = []
        
        # Add some sample revenue/expense data
        self.revenue_expenses = [
            {'date': today - timedelta(days=1), 'type': 'revenue', 'amount': 250.0, 'description': 'Egg sales'},
            {'date': today - timedelta(days=2), 'type': 'expense', 'amount': 150.0, 'description': 'Feed purchase'},
            {'date': today - timedelta(days=3), 'type': 'revenue', 'amount': 300.0, 'description': 'Chicken sales'},
            {'date': today - timedelta(days=4), 'type': 'expense', 'amount': 80.0, 'description': 'Veterinary visit'},
        ]
        
        # Initialize user progress
        self.user_points = 85
        self.user_level = 2
        self.user_badges = ['Early Bird', 'Health Champion']
    
    def complete_task(self, task_id):
        """Mark a task as completed and award points"""
        today = datetime.now().date()
        if today not in self.tasks:
            return False
            
        for task in self.tasks[today]:
            if task['id'] == task_id and task_id not in self.completed_tasks.get(today, []):
                self.completed_tasks[today].append(task_id)
                self.user_points += task['points']
                
                # Check for level up
                if self.user_points >= 100 * self.user_level:
                    self.user_level += 1
                    self.user_badges.append(f'Level {self.user_level} Master')
                
                return True
        return False
    
    def get_gamification_data(self):
        """Get user progress and gamification data"""
        today = datetime.now().date()
        total_tasks = len(self.tasks.get(today, []))
        completed_tasks = len(self.completed_tasks.get(today, []))
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'points': self.user_points,
            'level': self.user_level,
            'badges': self.user_badges,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': completion_rate,
            'next_level_points': 100 * self.user_level
        }
    
    def get_today_tasks(self):
        """Get today's tasks with completion status"""
        today = datetime.now().date()
        tasks = self.tasks.get(today, [])
        completed = self.completed_tasks.get(today, [])
        
        for task in tasks:
            task['completed'] = task['id'] in completed
        
        return tasks
    
    def add_revenue_expense(self, date, type_val, amount, description):
        """Add revenue or expense entry"""
        self.revenue_expenses.append({
            'date': date,
            'type': type_val,
            'amount': float(amount),
            'description': description
        })
    
    def get_financial_summary(self):
        """Get financial summary with profit/loss calculation"""
        total_revenue = sum(item['amount'] for item in self.revenue_expenses if item['type'] == 'revenue')
        total_expenses = sum(item['amount'] for item in self.revenue_expenses if item['type'] == 'expense')
        profit_loss = total_revenue - total_expenses
        
        return {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'profit_loss': profit_loss,
            'recent_entries': sorted(self.revenue_expenses, key=lambda x: x['date'], reverse=True)[:5]
        }
    
    def search_diseases(self, query):
        """Search diseases database"""
        if not query:
            return self.diseases_db
        
        query = query.lower()
        results = []
        for disease in self.diseases_db:
            if (query in disease['name'].lower() or 
                query in disease['symptoms'].lower() or 
                query in disease['treatment'].lower()):
                results.append(disease)
        
        return results
    
    def get_farm_health_status(self):
        """Get current farm health status"""
        today = datetime.now().date()
        completed = len(self.completed_tasks.get(today, []))
        total = len(self.tasks.get(today, []))
        
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
    
    def add_farm_visit(self):
        """Increment farm visit counter"""
        self.farm_visits += 1
        return self.farm_visits
    
    def add_chat_message(self, sender, message, sender_type='farmer'):
        """Add message to chat"""
        self.chat_messages.append({
            'timestamp': datetime.now(),
            'sender': sender,
            'message': message,
            'sender_type': sender_type
        })
    
    def get_chat_messages(self):
        """Get chat messages"""
        return self.chat_messages
    
    def check_temperature_alerts(self):
        """Check for temperature alerts (simulated)"""
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
            self.temperature_alerts.append(alert)
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
