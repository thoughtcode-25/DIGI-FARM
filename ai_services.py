# AI Services for Poultry Farm Management System
# Integration with OpenAI for chat assistance and disease detection

import json
import os
import base64
import logging
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai

class AIServices:
    """AI services for farmer assistance and disease detection"""
    
    def __init__(self):
        # Initialize available AI providers
        self.providers = {}
        
        # Setup OpenAI
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            self.providers['openai'] = OpenAI(api_key=openai_key)
        
        # Setup Google Gemini
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.providers['gemini'] = genai.GenerativeModel('gemini-1.5-flash')
        
        # Set preferred provider (Gemini first for cost savings, fallback to OpenAI)
        if 'gemini' in self.providers:
            self.primary_provider = 'gemini'
        elif 'openai' in self.providers:
            self.primary_provider = 'openai'
        else:
            raise ValueError("Either GEMINI_API_KEY or OPENAI_API_KEY environment variable is required")
        
        logging.info(f"AI Services initialized with {self.primary_provider} as primary provider")
        
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
            prompt = self.poultry_context + "\n\n"
            if context:
                prompt += f"Context: {context}\n\n"
            prompt += f"Question: {farmer_question}\n\nPlease provide practical farming advice:"
            
            # Try Gemini first (cost-effective)
            if self.primary_provider == 'gemini' and 'gemini' in self.providers:
                try:
                    response = self.providers['gemini'].generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=500,
                            temperature=0.7,
                        )
                    )
                    return {
                        "success": True,
                        "advice": response.text,
                        "timestamp": datetime.now().isoformat(),
                        "provider": "gemini"
                    }
                except Exception as gemini_error:
                    logging.warning(f"Gemini API error: {str(gemini_error)}")
            
            # Fallback to OpenAI if available
            if 'openai' in self.providers:
                messages = [
                    {"role": "system", "content": self.poultry_context},
                    {"role": "user", "content": prompt}
                ]
                
                response = self.providers['openai'].chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
                
                return {
                    "success": True,
                    "advice": response.choices[0].message.content,
                    "timestamp": datetime.now().isoformat(),
                    "provider": "openai"
                }
                
        except Exception as e:
            logging.error(f"All AI providers failed: {str(e)}")
            
        # Provide helpful farming advice as fallback
        fallback_advice = self._get_fallback_advice(farmer_question)
        return {
            "success": True,  # Don't show error to user, provide fallback
            "advice": fallback_advice,
            "timestamp": datetime.now().isoformat(),
            "provider": "fallback",
            "note": "This is general farming advice. For specific issues, please consult with a veterinarian."
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
            
            response = None
            
            # Try Gemini first for vision analysis (cost-effective)
            if self.primary_provider == 'gemini' and 'gemini' in self.providers:
                try:
                    # Convert base64 to image for Gemini
                    import io
                    from PIL import Image
                    image_data = base64.b64decode(image_base64)
                    image = Image.open(io.BytesIO(image_data))
                    
                    response = self.providers['gemini'].generate_content(
                        [disease_prompt, image],
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=800,
                            temperature=0.3,
                        )
                    )
                    
                    if response and response.text:
                        content = response.text
                        provider_used = "gemini"
                    else:
                        raise Exception("Gemini vision analysis failed")
                        
                except Exception as gemini_error:
                    logging.warning(f"Gemini vision analysis error: {str(gemini_error)}")
                    response = None
            
            # Fallback to OpenAI vision models
            if not response and 'openai' in self.providers:
                vision_models = ["gpt-4-turbo", "gpt-4o", "gpt-4-vision-preview"]
                
                for model in vision_models:
                    try:
                        response = self.providers['openai'].chat.completions.create(
                            model=model,
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
                        content = response.choices[0].message.content
                        provider_used = f"openai-{model}"
                        break
                    except Exception as model_error:
                        logging.warning(f"Vision model {model} failed: {str(model_error)}") 
                        continue
                        
            if not response:
                raise Exception("All vision models failed")
            
            # Try to parse JSON response
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
            analysis["provider"] = provider_used
            
            return analysis
            
        except Exception as e:
            logging.error(f"Disease image analysis error: {str(e)}")
            return {
                "success": True,  # Don't show error to user
                "disease_detected": True,
                "confidence_level": 0,
                "potential_diseases": ["Unable to analyze image - API temporarily unavailable"],
                "symptoms_visible": ["Please describe symptoms manually"],
                "recommendations": [
                    "Image analysis is currently unavailable",
                    "Monitor birds closely for signs of illness", 
                    "Contact veterinarian if birds show lethargy, loss of appetite, or unusual behavior",
                    "Maintain biosecurity measures as a precaution"
                ],
                "urgency_level": "medium",
                "should_contact_vet": True,
                "note": "For accurate diagnosis, please consult a veterinarian with physical examination"
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
    
    def _get_fallback_advice(self, question):
        """Provide fallback advice when API is not available"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['disease', 'prevention', 'health', 'sick']):
            return """**Disease Prevention Guidelines:**

            🔸 **Daily Tasks:**
            - Check birds for signs of illness (lethargy, loss of appetite, unusual behavior)
            - Ensure clean water is available at all times
            - Monitor feed consumption and quality
            - Remove any sick or dead birds immediately

            🔸 **Biosecurity Measures:**
            - Disinfect equipment and footwear before entering poultry area
            - Limit visitor access to your farm
            - Quarantine new birds for 2-3 weeks before mixing
            - Keep wild birds away from your poultry

            🔸 **Vaccination Schedule:**
            - Consult with your local veterinarian for region-specific vaccination program
            - Common vaccines: Newcastle Disease, Avian Influenza, Infectious Bronchitis
            - Follow proper vaccine storage and administration guidelines

            **Note:** This is general advice. For specific health concerns, always consult a veterinarian."""
            
        elif any(word in question_lower for word in ['nutrition', 'feed', 'food', 'diet']):
            return """**Poultry Nutrition Guidelines:**

            🔸 **Feed Requirements:**
            - Provide balanced commercial poultry feed appropriate for bird age
            - Starter feed (0-8 weeks): 20-24% protein
            - Grower feed (8-16 weeks): 16-18% protein
            - Layer feed (16+ weeks): 14-16% protein

            🔸 **Water Management:**
            - Fresh, clean water available 24/7
            - Check water quality regularly
            - Clean waterers daily

            🔸 **Feeding Tips:**
            - Feed 2-3 times daily at regular times
            - Store feed in dry, cool, rodent-proof containers
            - Check feed quality - avoid moldy or stale feed

            **Consult a poultry nutritionist for specific dietary requirements.**"""
            
        elif any(word in question_lower for word in ['biosecurity', 'safety', 'hygiene']):
            return """**Biosecurity Best Practices:**

            🔸 **Entry Controls:**
            - Single entry/exit point to poultry area
            - Foot baths with disinfectant at entry points
            - Dedicated clothing and footwear for poultry area
            - Hand washing facilities

            🔸 **Equipment Management:**
            - Regular cleaning and disinfection of equipment
            - Separate tools for different age groups
            - Proper disposal of dead birds and waste

            🔸 **Visitor Management:**
            - Limit unnecessary visitors
            - Maintain visitor log
            - Provide protective clothing for essential visitors

            **Strong biosecurity is your first line of defense against diseases.**"""
            
        else:
            return """**General Poultry Farming Tips:**

            🔸 **Daily Management:**
            - Check birds morning and evening
            - Monitor environmental conditions (temperature, ventilation)
            - Record keeping for health, production, and feed consumption
            - Maintain clean, dry bedding

            🔸 **Health Monitoring:**
            - Watch for signs of illness or stress
            - Regular health assessments
            - Build relationships with local veterinarians
            - Keep vaccination records up to date

            🔸 **Production Optimization:**
            - Maintain consistent lighting schedules
            - Ensure proper ventilation
            - Provide adequate space per bird
            - Monitor and record production data

            **For specific questions, please consult with poultry specialists or veterinarians in your area.**"""