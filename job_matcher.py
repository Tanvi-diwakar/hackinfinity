from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd

class JobMatcher:
    def __init__(self):
        # Use multilingual model for Indian languages
        self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        self.job_embeddings = None
        self.jobs_df = None
    
    def add_jobs(self, jobs_data):
        """Add job listings to the matcher"""
        self.jobs_df = pd.DataFrame(jobs_data)
        job_texts = self.jobs_df['description'].tolist()
        self.job_embeddings = self.model.encode(job_texts)
    
    def find_similar_jobs(self, query_text, top_k=5):
        """Find similar jobs based on text similarity"""
        if self.job_embeddings is None:
            return []
        
        query_embedding = self.model.encode([query_text])
        similarities = cosine_similarity(query_embedding, self.job_embeddings)[0]
        
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'job': self.jobs_df.iloc[idx].to_dict(),
                'similarity': similarities[idx]
            })
        
        return results
    
    def match_profile_to_jobs(self, profile, filters=None):
        """Match user profile to available jobs"""
        profile_text = f"{profile.get('skills', '')} {profile.get('experience', '')} {profile.get('preferences', '')}"
        
        similar_jobs = self.find_similar_jobs(profile_text)
        
        # Apply filters
        if filters:
            filtered_jobs = []
            for job_match in similar_jobs:
                job = job_match['job']
                
                # Location filter
                if filters.get('location') and job.get('location'):
                    if filters['location'].lower() not in job['location'].lower():
                        continue
                
                # Salary filter
                if filters.get('min_salary') and job.get('min_salary'):
                    if job['min_salary'] < filters['min_salary']:
                        continue
                
                filtered_jobs.append(job_match)
            
            return filtered_jobs
        
        return similar_jobs

# Usage example
if __name__ == "__main__":
    # Sample job data
    jobs_data = [
        {
            'id': 1,
            'title': 'Electrician Required',
            'description': 'Experienced electrician needed for residential wiring work in Mumbai',
            'location': 'Mumbai',
            'min_salary': 15000,
            'max_salary': 25000
        },
        {
            'id': 2,
            'title': 'Driver Position',
            'description': 'Truck driver needed for goods transportation across Maharashtra',
            'location': 'Pune',
            'min_salary': 18000,
            'max_salary': 22000
        }
    ]
    
    matcher = JobMatcher()
    matcher.add_jobs(jobs_data)
    
    # User profile
    user_profile = {
        'skills': 'electrical work, house wiring',
        'experience': '3 years electrician',
        'preferences': 'Mumbai location preferred'
    }
    
    # Find matching jobs
    matches = matcher.match_profile_to_jobs(
        user_profile, 
        filters={'location': 'Mumbai', 'min_salary': 10000}
    )
    
    for match in matches:
        print(f"Job: {match['job']['title']}")
        print(f"Similarity: {match['similarity']:.3f}")
        print(f"Location: {match['job']['location']}")
        print("-" * 30)