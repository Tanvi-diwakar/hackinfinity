import requests
import json

class JobAPIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def analyze_job(self, job_description):
        """Analyze a job description"""
        response = requests.post(
            f"{self.base_url}/analyze-job",
            json={"job_description": job_description}
        )
        return response.json()
    
    def get_jobs(self, location=None, category=None, min_salary=None, limit=10):
        """Get filtered job listings"""
        params = {"limit": limit}
        if location:
            params["location"] = location
        if category:
            params["category"] = category
        if min_salary:
            params["min_salary"] = min_salary
        
        response = requests.get(f"{self.base_url}/jobs", params=params)
        return response.json()
    
    def scrape_jobs(self):
        """Trigger job scraping"""
        response = requests.post(f"{self.base_url}/scrape-jobs")
        return response.json()
    
    def get_categories(self):
        """Get available job categories"""
        response = requests.get(f"{self.base_url}/categories")
        return response.json()
    
    def get_stats(self):
        """Get job statistics"""
        response = requests.get(f"{self.base_url}/stats")
        return response.json()
    
    def match_jobs(self, skills, experience, preferred_location=None, min_salary=None):
        """Match user profile to jobs"""
        data = {
            "skills": skills,
            "experience": experience
        }
        if preferred_location:
            data["preferred_location"] = preferred_location
        if min_salary:
            data["min_salary"] = min_salary
        
        response = requests.post(f"{self.base_url}/match-jobs", json=data)
        return response.json()

# Example usage
if __name__ == "__main__":
    client = JobAPIClient()
    
    # Test job analysis
    print("=== Job Analysis ===")
    result = client.analyze_job("Electrician needed for residential wiring in Mumbai. Salary ₹20,000 per month.")
    print(json.dumps(result, indent=2))
    
    # Test job search
    print("\n=== Job Search ===")
    jobs = client.get_jobs(location="Mumbai", limit=3)
    print(f"Found {jobs['total']} jobs")
    for job in jobs['jobs'][:2]:
        print(f"- {job['title']} in {job['location']}")
    
    # Test categories
    print("\n=== Categories ===")
    categories = client.get_categories()
    print(f"Available categories: {categories['categories'][:5]}...")
    
    # Test stats
    print("\n=== Statistics ===")
    stats = client.get_stats()
    print(f"Total jobs: {stats['total_jobs']}")
    print(f"Average salary: ₹{stats['average_salary']:.0f}")
    
    # Test job matching
    print("\n=== Job Matching ===")
    matches = client.match_jobs(
        skills="electrical work, wiring",
        experience="2 years electrician",
        preferred_location="Mumbai"
    )
    print(f"Found {matches['total_matches']} matching jobs")