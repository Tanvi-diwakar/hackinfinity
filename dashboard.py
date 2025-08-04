import streamlit as st
import pandas as pd
from skill_india_scraper import SkillIndiaScraper
import json
import os

st.set_page_config(page_title="Job Classification Dashboard", layout="wide")

# Enhanced job classifier with more categories
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
        
        # Find best matching category
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
        
        # Extract salary with multiple patterns
        import re
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
        
        # Extract location with more cities
        cities = ['mumbai', 'delhi', 'bangalore', 'chennai', 'pune', 'hyderabad', 
                 'ahmedabad', 'kolkata', 'jaipur', 'lucknow', 'kanpur', 'nagpur',
                 'indore', 'thane', 'bhopal', 'visakhapatnam', 'pimpri', 'patna']
        location = next((city.title() for city in cities if city in text_lower), None)
        
        # Enhanced scam detection
        scam_indicators = [
            'work from home guaranteed', 'no experience high salary', 'earn lakhs',
            'investment required', 'registration fee', 'advance payment',
            'part time full salary', 'easy money', 'get rich quick'
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



@st.cache_data
def load_jobs():
    """Load jobs from file or scrape new ones"""
    if os.path.exists('scraped_jobs.json'):
        with open('scraped_jobs.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        scraper = SkillIndiaScraper()
        jobs = scraper.scrape_jobs()
        scraper.save_jobs()
        return jobs

@st.cache_resource
def load_classifier():
    return EnhancedJobClassifier()

def main():
    st.title("🔍 Job Classification & Matching Dashboard")
    
    classifier = load_classifier()
    jobs_data = load_jobs()
    
    # Sidebar
    st.sidebar.header("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Browse Jobs", "Job Analysis", "Job Matching", "Analytics"])
    
    # Scraping controls
    st.sidebar.header("Data Management")
    if st.sidebar.button("🔄 Refresh Jobs"):
        if os.path.exists('scraped_jobs.json'):
            os.remove('scraped_jobs.json')
        st.cache_data.clear()
        st.rerun()
    
    st.sidebar.metric("Total Jobs", len(jobs_data))
    
    if page == "Browse Jobs":
        st.header("📋 Browse Scraped Jobs")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            location_filter = st.selectbox("Filter by Location", 
                ["All"] + list(set([job['location'] for job in jobs_data])))
        with col2:
            search_term = st.text_input("Search in job titles:")
        with col3:
            jobs_per_page = st.selectbox("Jobs per page", [5, 10, 20], index=1)
        
        # Filter jobs
        filtered_jobs = jobs_data
        if location_filter != "All":
            filtered_jobs = [job for job in filtered_jobs if job['location'] == location_filter]
        if search_term:
            filtered_jobs = [job for job in filtered_jobs if search_term.lower() in job['title'].lower()]
        
        st.write(f"Showing {len(filtered_jobs)} jobs")
        
        # Display jobs
        for i, job in enumerate(filtered_jobs[:jobs_per_page]):
            with st.expander(f"{job['title']} - {job['location']}"):
                st.write(f"**Description:** {job['description']}")
                st.write(f"**Location:** {job['location']}")
                st.write(f"**Source:** {job['source']}")
                
                if st.button(f"Analyze Job {i+1}", key=f"analyze_{job['id']}"):
                    result = classifier.analyze_job(job['description'])
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Predicted Category", result['category'])
                        st.metric("Confidence", f"{result['confidence']:.1%}")
                    with col_b:
                        if result['salary_range'] and result['salary_range'][0]:
                            st.metric("Extracted Salary", f"₹{result['salary_range'][0]:,}")
                        if result['is_suspicious']:
                            st.error("⚠️ Suspicious posting detected!")
                        else:
                            st.success("✅ Looks legitimate")
    
    elif page == "Job Analysis":
        st.header("📝 Job Description Analysis")
        
        job_text = st.text_area("Enter job description:", height=150)
        
        if st.button("Analyze Job"):
            if job_text:
                result = classifier.analyze_job(job_text)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Category", result['category'])
                    st.metric("Confidence", f"{result['confidence']:.2%}")
                
                with col2:
                    if result['salary_range'] and result['salary_range'][0]:
                        st.metric("Salary Range", f"₹{result['salary_range'][0]:,} - ₹{result['salary_range'][1]:,}")
                    if result['location']:
                        st.metric("Location", result['location'])
                
                if result['is_suspicious']:
                    st.error("⚠️ This job posting shows suspicious patterns!")
                else:
                    st.success("✅ Job posting appears legitimate")
    

        st.header("🎯 Job Matching")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("User Profile")
            skills = st.text_input("Skills:")
            experience = st.text_input("Experience:")
            location_pref = st.text_input("Preferred Location:")
            min_salary = st.number_input("Minimum Salary:", min_value=0, value=10000)
        
        with col2:
            st.subheader("Sample Jobs")
            # This would typically come from a database
            sample_jobs = [
                "Electrician needed in Mumbai for residential work",
                "Driver required for delivery services in Delhi",
                "Plumber wanted for maintenance work in Bangalore"
            ]
            
            for i, job in enumerate(sample_jobs):
                if st.button(f"Analyze Job {i+1}"):
                    result = classifier.analyze_job(job)
                    st.write(f"**Category:** {result['category']}")
                    st.write(f"**Confidence:** {result['confidence']:.2%}")
    
    elif page == "Analytics":
        st.header("📊 Job Market Analytics")
        
        # Sample data for visualization
        sample_data = pd.DataFrame({
            'Category': ['Electrician', 'Driver', 'Plumber', 'Sweeper'],
            'Count': [45, 32, 28, 15],
            'Avg_Salary': [18000, 16000, 15000, 12000]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Job Postings by Category")
            st.bar_chart(sample_data.set_index('Category')['Count'])
        
        with col2:
            st.subheader("Average Salary by Category")
            st.bar_chart(sample_data.set_index('Category')['Avg_Salary'])
        
        st.subheader("Job Statistics")
        st.dataframe(sample_data)

if __name__ == "__main__":
    main()