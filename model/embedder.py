from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache
import streamlit as st

model = SentenceTransformer('all-MiniLM-L6-v2')  # Small and fast

@lru_cache(maxsize=100)
def get_embedding(text):
    """Cache frequent embeddings to improve performance"""
    return model.encode([text])[0]

class EnhancedEmbedder:
    def __init__(self):
        self.model = model
        
        # Cuisine embeddings (learned from recipe patterns)
        self.cuisine_weights = {
            'Desi': [0.8, 0.6, 0.9],  # comfort, spice, family
            'Arabic': [0.7, 0.5, 0.8], 
            'Western': [0.5, 0.3, 0.6]
        }
        
        # Time-of-day embeddings
        self.time_weights = {
            'Breakfast': [0.6, 0.8, 0.4],  # light, energizing, quick
            'Lunch': [0.7, 0.6, 0.8],
            'Dinner': [0.9, 0.4, 0.7]  # comfort, heavy, social
        }
    
    def get_enhanced_embedding(self, description, cuisine, meal_time, cook_time):
        """Get enhanced embedding combining text, cuisine, time, and cooking duration"""
        # Text embedding
        text_emb = get_embedding(description)
        
        # Feature embeddings
        cuisine_emb = self.cuisine_weights.get(cuisine, [0.5, 0.5, 0.5])
        time_emb = self.time_weights.get(meal_time, [0.5, 0.5, 0.5])
        
        # Normalize cook time to 0-1
        time_factor = min(cook_time / 60, 1.0)
        
        # Combine embeddings (you can experiment with weights)
        enhanced = np.concatenate([
            text_emb * 0.7,  # Primary weight on description
            np.array(cuisine_emb) * 0.2,
            np.array(time_emb) * 0.1,
            [time_factor * 0.1]
        ])
        
        return enhanced

# Keep the original function for backward compatibility
# get_embedding is already defined above with caching