from flask import Flask, request
from enhanced_job_classifier import EnhancedJobClassifier
import json

app = Flask(__name__)
classifier = EnhancedJobClassifier()

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    """Handle WhatsApp messages"""
    data = request.get_json()
    
    # Extract message (simplified - actual implementation depends on WhatsApp API)
    if 'messages' in data:
        for message in data['messages']:
            if message['type'] == 'text':
                user_message = message['text']['body']
                phone_number = message['from']
                
                # Process job search request
                if 'job' in user_message.lower():
                    response = process_job_query(user_message)
                    send_whatsapp_message(phone_number, response)
    
    return 'OK', 200

def process_job_query(message):
    """Process job-related queries"""
    if 'search' in message.lower() or 'find' in message.lower():
        # Extract job type from message
        job_types = ['electrician', 'driver', 'plumber', 'sweeper']
        found_type = None
        
        for job_type in job_types:
            if job_type in message.lower():
                found_type = job_type
                break
        
        if found_type:
            return f"🔍 Found jobs for {found_type}:\n\n1. {found_type.title()} needed in Mumbai - ₹15,000-20,000\n2. Experienced {found_type} required in Delhi - ₹18,000-25,000\n\nReply with job number for details!"
        else:
            return "Please specify job type: electrician, driver, plumber, or sweeper"
    
    else:
        # Analyze job description
        result = classifier.analyze_job(message)
        response = f"📝 Job Analysis:\n"
        response += f"Category: {result['category']}\n"
        response += f"Confidence: {result['confidence']:.1%}\n"
        
        if result['salary_range'] and result['salary_range'][0]:
            response += f"Salary: ₹{result['salary_range'][0]:,}-₹{result['salary_range'][1]:,}\n"
        
        if result['location']:
            response += f"Location: {result['location']}\n"
        
        if result['is_suspicious']:
            response += "⚠️ Warning: Suspicious job posting!"
        
        return response

def send_whatsapp_message(phone_number, message):
    """Send message via WhatsApp API (placeholder)"""
    # This would integrate with actual WhatsApp Business API
    print(f"Sending to {phone_number}: {message}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)