from datetime import datetime, timedelta
from collections import defaultdict
import qrcode
import io
import base64

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
