import os
import logging
import random
import string
import requests
from datetime import datetime, timedelta
from twilio.rest import Client

logging.basicConfig(level=logging.DEBUG)

class SMSService:
    """SMS service for sending OTP and alerts using Twilio"""
    
    def __init__(self):
        """Initialize Twilio client using Replit connector"""
        self.client = None
        self.phone_number = None
        
        # Try to get credentials from Replit connector
        try:
            credentials = self._get_connector_credentials()
            if credentials:
                self.client = Client(
                    credentials['api_key'],
                    credentials['api_key_secret'],
                    account_sid=credentials['account_sid']
                )
                self.phone_number = credentials['phone_number']
                logging.info(f"Twilio SMS service initialized successfully via Replit connector (Account: {credentials['account_sid'][:8]}...)")
            else:
                # Fallback to environment variables
                self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
                self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
                self.phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
                
                if all([self.account_sid, self.auth_token, self.phone_number]):
                    self.client = Client(self.account_sid, self.auth_token)
                    logging.info("Twilio SMS service initialized successfully via environment variables")
                else:
                    logging.warning("Twilio credentials not configured. SMS features will be disabled.")
        except Exception as e:
            logging.error(f"Failed to initialize Twilio client: {e}")
            self.client = None
        
        # In-memory storage for OTPs (in production, use Redis or database)
        self.otp_storage = {}
    
    def _get_connector_credentials(self):
        """Get Twilio credentials from Replit connector"""
        try:
            hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
            x_replit_token = None
            
            repl_identity = os.environ.get('REPL_IDENTITY')
            web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')
            
            if repl_identity:
                x_replit_token = 'repl ' + repl_identity
            elif web_repl_renewal:
                x_replit_token = 'depl ' + web_repl_renewal
            
            if not hostname or not x_replit_token:
                return None
            
            url = f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=twilio'
            headers = {
                'Accept': 'application/json',
                'X_REPLIT_TOKEN': x_replit_token
            }
            
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if data.get('items') and len(data['items']) > 0:
                settings = data['items'][0].get('settings', {})
                if settings.get('account_sid') and settings.get('api_key') and settings.get('api_key_secret'):
                    return {
                        'account_sid': settings['account_sid'],
                        'api_key': settings['api_key'],
                        'api_key_secret': settings['api_key_secret'],
                        'phone_number': settings.get('phone_number')
                    }
            return None
        except Exception as e:
            logging.error(f"Failed to get connector credentials: {e}")
            return None
    
    def generate_otp(self, length=6):
        """Generate a random OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    def store_otp(self, phone_number, otp, expiry_minutes=10):
        """Store OTP with expiry time"""
        expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)
        self.otp_storage[phone_number] = {
            'otp': otp,
            'expiry': expiry_time,
            'attempts': 0
        }
        logging.info(f"OTP stored for {phone_number}, expires at {expiry_time}")
    
    def verify_otp(self, phone_number, otp, max_attempts=3):
        """Verify OTP against stored value"""
        if phone_number not in self.otp_storage:
            return False, "No OTP found for this number"
        
        stored_data = self.otp_storage[phone_number]
        
        # Check if OTP has expired
        if datetime.now() > stored_data['expiry']:
            del self.otp_storage[phone_number]
            return False, "OTP has expired"
        
        # Check attempts
        if stored_data['attempts'] >= max_attempts:
            del self.otp_storage[phone_number]
            return False, "Maximum verification attempts exceeded"
        
        # Verify OTP
        if stored_data['otp'] == otp:
            del self.otp_storage[phone_number]
            return True, "OTP verified successfully"
        else:
            stored_data['attempts'] += 1
            return False, "Invalid OTP"
    
    def send_sms(self, to_number, message):
        """Send SMS using Twilio"""
        if not self.client:
            logging.warning(f"SMS not sent (Twilio not configured): {message[:50]}...")
            return False, "SMS service not configured"
        
        try:
            # Format phone number (ensure it has country code)
            if not to_number.startswith('+'):
                to_number = '+91' + to_number  # Default to India country code
            
            message_obj = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_number
            )
            
            logging.info(f"SMS sent successfully. SID: {message_obj.sid}")
            return True, "SMS sent successfully"
        
        except Exception as e:
            logging.error(f"Failed to send SMS: {e}")
            return False, f"Failed to send SMS: {str(e)}"
    
    def send_otp(self, phone_number, purpose="verification"):
        """Generate and send OTP via SMS"""
        otp = self.generate_otp()
        self.store_otp(phone_number, otp)
        
        message = f"Your OTP for farm {purpose} is: {otp}. Valid for 10 minutes. Do not share with anyone."
        
        success, msg = self.send_sms(phone_number, message)
        
        if success:
            logging.info(f"OTP sent to {phone_number} for {purpose}")
        else:
            logging.error(f"Failed to send OTP to {phone_number}: {msg}")
        
        return success, msg, otp if not success else None
    
    def send_flu_alert(self, phone_number, location, farm_name):
        """Send flu alert notification via SMS"""
        message = f"""ALERT: Avian Influenza detected near {location}. 
{farm_name}, please:
- Restrict farm access
- Monitor birds closely
- Report sick birds immediately
- Follow biosecurity protocols
Contact: 1800-XXX-XXXX"""
        
        success, msg = self.send_sms(phone_number, message)
        
        if success:
            logging.info(f"Flu alert sent to {phone_number} for location {location}")
        else:
            logging.error(f"Failed to send flu alert to {phone_number}: {msg}")
        
        return success, msg
    
    def send_disease_alert(self, phone_number, disease_name, location, farm_name, farm_type='chickens'):
        """Send disease alert notification via SMS"""
        animal = "poultry" if farm_type == 'chickens' else "pigs" if farm_type == 'pigs' else "livestock"
        
        message = f"""ALERT: {disease_name} detected near {location}. 
{farm_name}, please:
- Monitor {animal} health closely
- Implement strict biosecurity
- Report any sick animals
- Contact veterinarian
Emergency: 1800-XXX-XXXX"""
        
        success, msg = self.send_sms(phone_number, message)
        
        if success:
            logging.info(f"Disease alert sent to {phone_number} for {disease_name} at {location}")
        else:
            logging.error(f"Failed to send disease alert to {phone_number}: {msg}")
        
        return success, msg
