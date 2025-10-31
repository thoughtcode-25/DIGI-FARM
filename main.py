from app_init import app, db
import models  # noqa: F401

# Create database tables
with app.app_context():
    db.create_all()
    
    # Seed initial data if farm_statistics table is empty
    from models import FarmStatistics
    if FarmStatistics.query.count() == 0:
        # Initialize pig farming statistics
        pig_stats = FarmStatistics(
            farm_type='pigs',
            total_population=45000000,  # 45.0M
            registered_farms=5800,
            annual_production_mt=2.5,  # 2.5 Million Tonnes
            farmers_benefitted=1200000,  # 1.2M
            growth_rate=8.5  # 8.5% YoY
        )
        
        # Initialize poultry statistics
        poultry_stats = FarmStatistics(
            farm_type='chickens',
            total_population=851600000,  # 851.6M
            registered_farms=42500,
            annual_production_mt=12.8,  # 12.8 Million Tonnes eggs
            farmers_benefitted=3500000,  # 3.5M
            growth_rate=12.3  # 12.3% YoY
        )
        
        db.session.add(pig_stats)
        db.session.add(poultry_stats)
        db.session.commit()
        print("Database seeded with initial farm statistics")

# Import routes from app
from app import *  # noqa: F401, F403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
