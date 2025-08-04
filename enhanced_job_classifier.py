from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics.pairwise import cosine_similarity
import re
import pickle

class EnhancedJobClassifier:
    def __init__(self, model_path="./your-finetuned-model"):
        # Load transformer model
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        # Job categories
        self.labels = ["plumber", "driver", "sweeper", "electrician"]
        
        # Load RandomForest if available
        try:
            with open('rf_model.pkl', 'rb') as f:
                self.rf_model = pickle.load(f)
            with open('tfidf_vectorizer.pkl', 'rb') as f:
                self.vectorizer = pickle.load(f)
        except:
            self.rf_model = None
            self.vectorizer = None
    
    def predict_with_confidence(self, text):
        """Get prediction with confidence score"""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        probs = torch.softmax(outputs.logits, dim=1)
        confidence = torch.max(probs).item()
        pred_class = torch.argmax(outputs.logits, dim=1).item()
        
        return self.labels[pred_class], confidence
    
    def extract_salary_info(self, text):
        """Extract salary information from job description"""
        salary_patterns = [
            r'₹\s*(\d+(?:,\d+)*)\s*(?:-|to)\s*₹?\s*(\d+(?:,\d+)*)',
            r'(\d+(?:,\d+)*)\s*(?:-|to)\s*(\d+(?:,\d+)*)\s*(?:rs|rupees|₹)',
            r'salary\s*:?\s*₹?\s*(\d+(?:,\d+)*)',
            r'(\d+)k\s*(?:-|to)\s*(\d+)k'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text.lower())
            if match:
                if len(match.groups()) == 2:
                    min_sal = int(match.group(1).replace(',', ''))
                    max_sal = int(match.group(2).replace(',', ''))
                    if 'k' in pattern:
                        min_sal *= 1000
                        max_sal *= 1000
                    return min_sal, max_sal
                else:
                    sal = int(match.group(1).replace(',', ''))
                    return sal, sal
        return None, None
    
    def extract_location(self, text):
        """Extract location from job description"""
        indian_cities = ['mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata', 'hyderabad', 
                        'pune', 'ahmedabad', 'surat', 'jaipur', 'lucknow', 'kanpur']
        
        text_lower = text.lower()
        for city in indian_cities:
            if city in text_lower:
                return city.title()
        return None
    
    def detect_scam_indicators(self, text):
        """Detect potential scam job postings"""
        scam_keywords = ['work from home guaranteed', 'no experience needed high salary', 
                        'earn lakhs', 'part time full salary', 'investment required']
        
        suspicious_patterns = [
            r'earn\s+₹?\d+\s+lakhs?\s+monthly',
            r'no\s+work\s+high\s+salary',
            r'investment\s+of\s+₹?\d+'
        ]
        
        text_lower = text.lower()
        scam_score = 0
        
        for keyword in scam_keywords:
            if keyword in text_lower:
                scam_score += 1
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text_lower):
                scam_score += 2
        
        return scam_score > 2
    
    def analyze_job(self, job_text):
        """Comprehensive job analysis"""
        category, confidence = self.predict_with_confidence(job_text)
        min_salary, max_salary = self.extract_salary_info(job_text)
        location = self.extract_location(job_text)
        is_suspicious = self.detect_scam_indicators(job_text)
        
        return {
            'category': category,
            'confidence': confidence,
            'salary_range': (min_salary, max_salary) if min_salary else None,
            'location': location,
            'is_suspicious': is_suspicious,
            'text': job_text
        }

# Usage example
if __name__ == "__main__":
    classifier = EnhancedJobClassifier()
    
    test_jobs = [
        "Looking for an electrician to handle wiring issues in Mumbai. Salary ₹15,000-20,000",
        "Driver needed for delivery in Delhi. Experience required. Contact immediately.",
        "Work from home guaranteed! Earn ₹50,000 monthly with no experience needed!"
    ]
    
    for job in test_jobs:
        result = classifier.analyze_job(job)
        print(f"📝 Job: {job}")
        print(f"🔍 Category: {result['category']} (Confidence: {result['confidence']:.2f})")
        print(f"💰 Salary: {result['salary_range']}")
        print(f"📍 Location: {result['location']}")
        print(f"⚠️ Suspicious: {result['is_suspicious']}")
        print("-" * 50)