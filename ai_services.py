# AI Services for Poultry Farm Management System
# Integration with OpenAI for chat assistance and disease detection

import json
import os
import base64
from datetime import datetime
from openai import OpenAI

class AIServices:
    """AI services for farmer assistance and disease detection"""
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=self.api_key)
        
        # Poultry-specific knowledge base
        self.poultry_context = """
        You are an expert poultry farming AI assistant specialized in chicken farming, disease prevention, 
        biosecurity, nutrition, and farm management. You provide practical, actionable advice for poultry farmers
        in India focusing on:
        
        - Disease identification and prevention (Avian Influenza, Newcastle Disease, etc.)
        - Biosecurity protocols and sanitation
        - Nutrition and feed management
        - Farm infrastructure and housing
        - Production optimization
        - Government schemes and regulations
        - Market trends and selling strategies
        
        Always provide specific, practical advice suitable for Indian farming conditions.
        """
    
    def get_farming_advice(self, farmer_question, context=None):
        """Get AI-powered farming advice for any question"""
        try:
            messages = [
                {"role": "system", "content": self.poultry_context},
            ]
            
            if context:
                messages.append({"role": "user", "content": f"Context: {context}"})
            
            messages.append({"role": "user", "content": farmer_question})
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return {
                "success": True,
                "advice": response.choices[0].message.content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get farming advice: {str(e)}",
                "advice": "I'm currently unable to provide advice. Please try again later or consult with a veterinarian."
            }
    
    def analyze_disease_image(self, image_base64, symptoms_description=""):
        """Analyze uploaded image for disease detection"""
        try:
            disease_prompt = f"""
            Analyze this image of poultry birds for any signs of disease or health issues.
            Additional symptoms described by farmer: {symptoms_description}
            
            Please provide your analysis as a JSON object with these fields:
            - disease_detected: true or false
            - confidence_level: number from 0-100
            - potential_diseases: array of possible disease names
            - symptoms_visible: array of symptoms you can see
            - recommendations: array of action steps
            - urgency_level: "low", "medium", "high", or "critical"
            - should_contact_vet: true or false
            
            Focus on common poultry diseases like Newcastle Disease, Avian Influenza, Infectious Bronchitis, Coccidiosis.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": disease_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                            }
                        ]
                    }
                ],
                max_tokens=800
            )
            
            # Try to parse JSON response
            content = response.choices[0].message.content
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, create structured response
                analysis = {
                    "disease_detected": True,
                    "confidence_level": 75,
                    "potential_diseases": ["Analysis completed - see recommendations"],
                    "symptoms_visible": ["Please see detailed analysis below"],
                    "recommendations": [content],
                    "urgency_level": "medium",
                    "should_contact_vet": True
                }
            
            analysis["timestamp"] = datetime.now().isoformat()
            analysis["success"] = True
            
            return analysis
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze image: {str(e)}",
                "disease_detected": False,
                "confidence_level": 0,
                "recommendations": ["Image analysis failed. Please consult with a veterinarian for proper diagnosis."],
                "should_contact_vet": True
            }
    
    def analyze_iot_sensor_data(self, sensor_data):
        """Analyze IoT sensor data for disease prediction and farm optimization"""
        try:
            sensor_prompt = f"""
            Analyze this IoT sensor data from a poultry farm and provide insights.
            Sensor Data: {json.dumps(sensor_data, indent=2)}
            
            Please provide analysis as a JSON object with these fields:
            - overall_status: "good", "warning", or "critical"
            - temperature_status: analysis of temperature readings
            - humidity_status: analysis of humidity levels
            - disease_risk_level: "low", "medium", or "high"
            - recommendations: array of action items
            - alerts: array of immediate concerns
            
            Consider optimal ranges: Temperature 22-28°C, Humidity 50-70%
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.poultry_context},
                    {"role": "user", "content": sensor_prompt}
                ],
                max_tokens=600
            )
            
            # Try to parse JSON response
            content = response.choices[0].message.content
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, create structured response
                analysis = {
                    "overall_status": "warning",
                    "temperature_status": "Unable to parse detailed analysis",
                    "humidity_status": "Unable to parse detailed analysis", 
                    "disease_risk_level": "medium",
                    "recommendations": [content],
                    "alerts": ["Please review sensor data manually"]
                }
            
            analysis["timestamp"] = datetime.now().isoformat()
            analysis["success"] = True
            
            return analysis
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze sensor data: {str(e)}",
                "overall_status": "unknown",
                "recommendations": ["Unable to analyze sensor data. Please check manually."]
            }
    
    def get_disease_prevention_plan(self, farm_size, current_season=""):
        """Generate personalized disease prevention plan"""
        try:
            prevention_prompt = f"""
            Create a disease prevention plan for a poultry farm with {farm_size} birds.
            Current season: {current_season}
            
            Please provide a plan as a JSON object with these fields:
            - daily_tasks: array of daily biosecurity tasks
            - weekly_tasks: array of weekly maintenance tasks
            - monthly_tasks: array of monthly health checks
            - vaccination_schedule: array of recommended vaccinations
            - biosecurity_measures: array of key biosecurity protocols
            - seasonal_precautions: array of seasonal measures
            
            Focus on preventing Avian Influenza, Newcastle Disease, etc. for Indian conditions.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.poultry_context},
                    {"role": "user", "content": prevention_prompt}
                ],
                max_tokens=800
            )
            
            # Try to parse JSON response
            content = response.choices[0].message.content
            try:
                plan = json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, create structured response
                plan = {
                    "daily_tasks": ["Check water and feed quality", "Observe bird behavior", "Clean feeding areas"],
                    "weekly_tasks": ["Disinfect equipment", "Check ventilation systems"],
                    "monthly_tasks": ["Health assessment", "Record keeping review"],
                    "vaccination_schedule": ["Consult veterinarian for vaccination schedule"],
                    "biosecurity_measures": [content],
                    "seasonal_precautions": ["Follow seasonal guidelines as provided"]
                }
            
            plan["farm_size"] = farm_size
            plan["generated_date"] = datetime.now().isoformat()
            plan["success"] = True
            
            return plan
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate prevention plan: {str(e)}",
                "daily_tasks": ["Unable to generate plan. Please consult with a veterinarian."]
            }