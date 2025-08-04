from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from skill_india_scraper import SkillIndiaScraper
import re

app = FastAPI(title="Job Classification API", version="1.0.0")

# Enhanced job classifier
class EnhancedJobClassifier:
    def __init__(self):
        self.job_categories = {
            'electrician': ['electric', 'wiring', 'voltage', 'circuit', 'electrical', 'power'],
            'plumber': ['plumb', 'pipe', 'water', 'leak', 'bathroom', 'toilet', 'drainage'],
            'driver': ['drive', 'truck', 'delivery', 'transport', 'vehicle', 'auto', 'taxi'],
            'cleaner': ['clean', 'sweep', 'housekeep', 'janitor', 'sanitiz', 'maintenance'],
            'carpenter': ['carpent', 'wood', 'furniture', 'cabinet', 'door', 'window'],
            'mechanic': ['mechanic', 'repair', 'engine', 'motor', 'garage', 'service'],
            'security_guard': ['security', 'guard', 'watchman', 'safety', 'patrol'],
            'cook': ['cook', 'chef', 'kitchen', 'food', 'restaurant', 'catering'],
            'tailor': ['tailor', 'sewing', 'stitch', 'garment', 'cloth', 'alteration'],
            'construction_worker': ['construction', 'building', 'mason', 'labor', 'site'],
            'ac_technician': ['ac', 'air condition', 'cooling', 'hvac', 'refrigerat'],
            'beautician': ['beauty', 'salon', 'hair', 'makeup', 'facial', 'parlor'],
            'delivery_boy': ['delivery', 'courier', 'parcel', 'logistics', 'shipping'],
            'sales_executive': ['sales', 'marketing', 'customer', 'business', 'retail'],
            'data_entry': ['data entry', 'typing', 'computer', 'excel', 'office'],
            'teacher': ['teach', 'tutor', 'education', 'school', 'training', 'instructor'],
            'nurse': ['nurse', 'medical', 'hospital', 'healthcare', 'patient'],
            'accountant': ['account', 'finance', 'bookkeep', 'tax', 'audit'],
            'receptionist': ['reception', 'front desk', 'customer service', 'phone'],
            'warehouse_worker': ['warehouse', 'inventory', 'stock', 'packing', 'loading']
        }
    
    def analyze_job(self, text):
        text_lower = text.lower()
        
        category_scores = {}
        for category, keywords in self.job_categories.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            category = max(category_scores, key=category_scores.get)
            confidence = min(0.95, 0.6 + (category_scores[category] * 0.1))
        else:
            category = 'general'
            confidence = 0.3
        
        # Extract salary
        salary_patterns = [
            r'₹\s*(\d+(?:,\d+)*)',
            r'(\d+)k\s*(?:per|/)?\s*month',
            r'salary\s*:?\s*₹?\s*(\d+(?:,\d+)*)',
            r'(\d+(?:,\d+)*)\s*(?:rs|rupees)'
        ]
        
        salary = None
        for pattern in salary_patterns:
            match = re.search(pattern, text_lower)
            if match:
                sal_str = match.group(1).replace(',', '')
                salary = int(sal_str)
                if 'k' in pattern and 'k' in match.group(0):
                    salary *= 1000
                break
        
        # Extract location
        cities = ['mumbai', 'delhi', 'bangalore', 'chennai', 'pune', 'hyderabad', 
                 'ahmedabad', 'kolkata', 'jaipur', 'lucknow', 'kanpur', 'nagpur']
        location = next((city.title() for city in cities if city in text_lower), None)
        
        # Scam detection
        scam_indicators = [
            'work from home guaranteed', 'no experience high salary', 'earn lakhs',
            'investment required', 'registration fee', 'advance payment'
        ]
        is_suspicious = any(indicator in text_lower for indicator in scam_indicators)
        
        return {
            'category': category.replace('_', ' ').title(),
            'confidence': confidence,
            'salary_range': (salary, salary) if salary else None,
            'location': location,
            'is_suspicious': is_suspicious,
            'raw_category': category
        }

# Initialize classifier
classifier = EnhancedJobClassifier()

# Pydantic models
class JobAnalysisRequest(BaseModel):
    job_description: str

class JobAnalysisResponse(BaseModel):
    category: str
    confidence: float
    salary_range: Optional[tuple] = None
    location: Optional[str] = None
    is_suspicious: bool
    raw_category: str

class JobSearchRequest(BaseModel):
    location: Optional[str] = None
    category: Optional[str] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    limit: int = 10

class JobMatchRequest(BaseModel):
    skills: str
    experience: str
    preferred_location: Optional[str] = None
    min_salary: Optional[int] = None

# API endpoints
@app.get("/")
async def root():
    return {"message": "Job Classification API", "version": "1.0.0"}

@app.post("/analyze-job", response_model=JobAnalysisResponse)
async def analyze_job(request: JobAnalysisRequest):
    """Analyze a job description and classify it"""
    try:
        result = classifier.analyze_job(request.job_description)
        return JobAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs")
async def get_jobs(
    location: Optional[str] = None,
    category: Optional[str] = None,
    min_salary: Optional[int] = None,
    limit: int = 10
):
    """Get filtered job listings"""
    try:
        # Load jobs from file
        if os.path.exists('scraped_jobs.json'):
            with open('scraped_jobs.json', 'r', encoding='utf-8') as f:
                jobs = json.load(f)
        else:
            jobs = []
        
        # Apply filters
        filtered_jobs = jobs
        
        if location:
            filtered_jobs = [job for job in filtered_jobs 
                           if location.lower() in job.get('location', '').lower()]
        
        if category:
            filtered_jobs = [job for job in filtered_jobs 
                           if category.lower() in job.get('title', '').lower()]
        
        if min_salary:
            # Analyze each job to extract salary and filter
            salary_filtered = []
            for job in filtered_jobs:
                analysis = classifier.analyze_job(job.get('description', ''))
                if analysis['salary_range'] and analysis['salary_range'][0]:
                    if analysis['salary_range'][0] >= min_salary:
                        salary_filtered.append(job)
                else:
                    salary_filtered.append(job)  # Include jobs without salary info
            filtered_jobs = salary_filtered
        
        return {"jobs": filtered_jobs[:limit], "total": len(filtered_jobs)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape-jobs")
async def scrape_new_jobs():
    """Scrape new jobs from Skill India"""
    try:
        scraper = SkillIndiaScraper()
        jobs = scraper.scrape_jobs()
        scraper.save_jobs()
        return {"message": f"Scraped {len(jobs)} jobs successfully", "jobs_count": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories")
async def get_job_categories():
    """Get all available job categories"""
    categories = list(classifier.job_categories.keys())
    return {"categories": [cat.replace('_', ' ').title() for cat in categories]}

@app.get("/stats")
async def get_job_stats():
    """Get job statistics"""
    try:
        if os.path.exists('scraped_jobs.json'):
            with open('scraped_jobs.json', 'r', encoding='utf-8') as f:
                jobs = json.load(f)
        else:
            jobs = []
        
        # Analyze all jobs
        category_counts = {}
        location_counts = {}
        salary_data = []
        
        for job in jobs:
            analysis = classifier.analyze_job(job.get('description', ''))
            
            # Count categories
            category = analysis['raw_category']
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Count locations
            location = job.get('location', 'Unknown')
            location_counts[location] = location_counts.get(location, 0) + 1
            
            # Collect salary data
            if analysis['salary_range'] and analysis['salary_range'][0]:
                salary_data.append(analysis['salary_range'][0])
        
        avg_salary = sum(salary_data) / len(salary_data) if salary_data else 0
        
        return {
            "total_jobs": len(jobs),
            "categories": category_counts,
            "locations": location_counts,
            "average_salary": avg_salary,
            "salary_jobs_count": len(salary_data)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/match-jobs")
async def match_jobs(request: JobMatchRequest):
    """Match user profile to available jobs"""
    try:
        if os.path.exists('scraped_jobs.json'):
            with open('scraped_jobs.json', 'r', encoding='utf-8') as f:
                jobs = json.load(f)
        else:
            jobs = []
        
        # Simple matching based on keywords
        profile_keywords = (request.skills + " " + request.experience).lower().split()
        
        matched_jobs = []
        for job in jobs:
            job_text = (job.get('title', '') + " " + job.get('description', '')).lower()
            
            # Calculate match score
            match_score = sum(1 for keyword in profile_keywords if keyword in job_text)
            
            if match_score > 0:
                # Apply filters
                if request.preferred_location:
                    if request.preferred_location.lower() not in job.get('location', '').lower():
                        continue
                
                if request.min_salary:
                    analysis = classifier.analyze_job(job.get('description', ''))
                    if analysis['salary_range'] and analysis['salary_range'][0]:
                        if analysis['salary_range'][0] < request.min_salary:
                            continue
                
                matched_jobs.append({
                    "job": job,
                    "match_score": match_score,
                    "analysis": classifier.analyze_job(job.get('description', ''))
                })
        
        # Sort by match score
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return {"matched_jobs": matched_jobs[:10], "total_matches": len(matched_jobs)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)