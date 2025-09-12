# AI Services for Poultry Farm Management System
# Integration with OpenAI for chat assistance and disease detection

import json
import os
import base64
from datetime import datetime

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
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
                model="gpt-5",
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
            You are a veterinary expert specializing in poultry diseases. Analyze this image of poultry birds 
            for any signs of disease or health issues.
            
            Additional symptoms described by farmer: {symptoms_description}
            
            Provide analysis in JSON format with:
            - disease_detected: true/false
            - confidence_level: 0-100
            - potential_diseases: list of possible diseases
            - symptoms_visible: list of symptoms you can see
            - recommendations: immediate action steps
            - urgency_level: low/medium/high/critical
            - should_contact_vet: true/false
            
            Focus on common poultry diseases like Newcastle Disease, Avian Influenza, 
            Infectious Bronchitis, Coccidiosis, etc.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-5",
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
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
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
            Analyze this IoT sensor data from a poultry farm and provide insights:
            
            Sensor Data: {json.dumps(sensor_data, indent=2)}
            
            Provide analysis in JSON format with:
            - overall_status: good/warning/critical
            - temperature_status: analysis of temperature readings
            - humidity_status: analysis of humidity levels
            - air_quality_status: if available
            - disease_risk_level: low/medium/high
            - recommendations: list of action items
            - alerts: any immediate concerns
            - optimization_tips: suggestions for improvement
            
            Consider optimal ranges for poultry:
            - Temperature: 22-28°C for adult chickens
            - Humidity: 50-70%
            - Good ventilation and air quality
            """
            
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": self.poultry_context},
                    {"role": "user", "content": sensor_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=600
            )
            
            analysis = json.loads(response.choices[0].message.content)
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
            Create a comprehensive disease prevention plan for a poultry farm with {farm_size} birds.
            Current season/time: {current_season}
            
            Provide a detailed plan in JSON format with:
            - daily_tasks: list of daily biosecurity tasks
            - weekly_tasks: list of weekly maintenance tasks
            - monthly_tasks: list of monthly health checks
            - vaccination_schedule: recommended vaccination timeline
            - biosecurity_measures: key biosecurity protocols
            - seasonal_precautions: specific measures for current season
            - emergency_contacts: types of contacts to have ready
            - monitoring_checklist: what to monitor daily
            
            Focus on preventing common diseases like Avian Influenza, Newcastle Disease, etc.
            Tailor advice for Indian farming conditions.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": self.poultry_context},
                    {"role": "user", "content": prevention_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=800
            )
            
            plan = json.loads(response.choices[0].message.content)
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