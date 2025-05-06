import redis
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import time
import random
from datetime import datetime, timedelta
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AnalyticsCollector:
    def __init__(self):
        # Initialize Redis connection
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0
        )
        
        # Initialize MongoDB connection
        self.mongo_client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
        self.db = self.mongo_client['chatbot_analytics']
        
        # Initialize counters
        self.message_count = 0
        self.active_users = 1
        self.api_cost = 0.10
        self.rate_limit = 100
        
        # Start background threads
        self.start_collectors()
    
    def start_collectors(self):
        # Start message collector
        threading.Thread(target=self.collect_messages, daemon=True).start()
        
        # Start user activity collector
        threading.Thread(target=self.collect_user_activity, daemon=True).start()
        
        # Start API cost collector
        threading.Thread(target=self.collect_api_costs, daemon=True).start()
        
        # Start rate limit collector
        threading.Thread(target=self.collect_rate_limits, daemon=True).start()
    
    def collect_messages(self):
        while True:
            try:
                # Simulate message volume with realistic patterns
                hour = datetime.now().hour
                if 9 <= hour <= 17:  # Business hours
                    messages = random.randint(5, 15)
                elif 18 <= hour <= 22:  # Evening peak
                    messages = random.randint(8, 20)
                else:  # Off hours
                    messages = random.randint(0, 5)
                
                self.message_count += messages
                
                # Store in Redis
                self.redis_client.set('total_messages', self.message_count)
                
                # Store in MongoDB
                self.db.message_logs.insert_one({
                    'timestamp': datetime.now(),
                    'count': messages
                })
                
                logger.info(f"Collected {messages} new messages")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in message collector: {e}")
                time.sleep(5)
    
    def collect_user_activity(self):
        while True:
            try:
                # Simulate user activity with realistic patterns
                hour = datetime.now().hour
                day = datetime.now().weekday()
                
                # Base users based on time of day
                if 9 <= hour <= 17:  # Business hours
                    base_users = 20
                elif 18 <= hour <= 22:  # Evening peak
                    base_users = 30
                else:  # Off hours
                    base_users = 10
                
                # Adjust for weekends
                if day >= 5:  # Weekend
                    base_users = int(base_users * 0.7)
                
                # Add some randomness
                self.active_users = base_users + random.randint(-5, 5)
                
                # Store in Redis
                self.redis_client.set('active_users', self.active_users)
                
                # Store in MongoDB
                self.db.user_activity.insert_one({
                    'timestamp': datetime.now(),
                    'count': self.active_users
                })
                
                logger.info(f"Active users: {self.active_users}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in user activity collector: {e}")
                time.sleep(5)
    
    def collect_api_costs(self):
        while True:
            try:
                # Simulate API costs with realistic patterns
                hour = datetime.now().hour
                if 9 <= hour <= 17:  # Business hours
                    cost_increment = random.uniform(0.05, 0.15)
                elif 18 <= hour <= 22:  # Evening peak
                    cost_increment = random.uniform(0.08, 0.20)
                else:  # Off hours
                    cost_increment = random.uniform(0.02, 0.08)
                
                self.api_cost += cost_increment
                
                # Store in Redis
                self.redis_client.set('api_cost', self.api_cost)
                
                # Store in MongoDB
                self.db.api_costs.insert_one({
                    'timestamp': datetime.now(),
                    'cost': self.api_cost
                })
                
                logger.info(f"API cost: ${self.api_cost:.2f}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in API cost collector: {e}")
                time.sleep(5)
    
    def collect_rate_limits(self):
        while True:
            try:
                # Simulate rate limit usage with realistic patterns
                hour = datetime.now().hour
                if 9 <= hour <= 17:  # Business hours
                    rate_change = random.randint(-3, 1)
                elif 18 <= hour <= 22:  # Evening peak
                    rate_change = random.randint(-5, 0)
                else:  # Off hours
                    rate_change = random.randint(0, 2)
                
                self.rate_limit = max(80, min(100, self.rate_limit + rate_change))
                
                # Store in Redis
                self.redis_client.set('rate_limit', self.rate_limit)
                
                # Store in MongoDB
                self.db.rate_limits.insert_one({
                    'timestamp': datetime.now(),
                    'remaining': self.rate_limit
                })
                
                logger.info(f"Rate limit: {self.rate_limit}%")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in rate limit collector: {e}")
                time.sleep(5)

if __name__ == '__main__':
    collector = AnalyticsCollector()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping data collector...") 