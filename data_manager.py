from datetime import datetime, timedelta
from collections import defaultdict

class DataManager:
    """Manages in-memory data storage for the poultry farm application"""
    
    def __init__(self):
        # In-memory storage using dictionaries and lists
        self.daily_data = {}  # date -> {chickens, eggs, feed, expenses}
        self.initialize_sample_data()
    
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
