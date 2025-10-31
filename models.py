from app_init import db
from datetime import datetime


class FarmStatistics(db.Model):
    """Model for storing real-time farm statistics"""
    __tablename__ = 'farm_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    farm_type = db.Column(db.String(50), nullable=False)  # 'pigs', 'chickens', 'both'
    total_population = db.Column(db.BigInteger, nullable=False)
    registered_farms = db.Column(db.Integer, nullable=False)
    annual_production_mt = db.Column(db.Float, nullable=True)  # Million Tonnes
    farmers_benefitted = db.Column(db.Integer, nullable=True)
    growth_rate = db.Column(db.Float, nullable=True)  # Percentage
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FarmStatistics {self.farm_type}: {self.total_population}>'
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'farm_type': self.farm_type,
            'total_population': self.total_population,
            'registered_farms': self.registered_farms,
            'annual_production_mt': self.annual_production_mt,
            'farmers_benefitted': self.farmers_benefitted,
            'growth_rate': self.growth_rate,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class User(db.Model):
    """Model for user authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'
