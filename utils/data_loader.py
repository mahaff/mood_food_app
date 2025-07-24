import pandas as pd
import streamlit as st
import pickle
import os
from pathlib import Path
import numpy as np
from config import PATHS, CACHE_CONFIG

class DataLoader:
    """Handles loading and caching of recipe data and embeddings"""
    
    def __init__(self):
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    @st.cache_data
    def load_recipes(_self):
        """Load recipe data with caching"""
        try:
            df = pd.read_csv(PATHS['data'])
            df["description"] = df["description"].fillna("")
            df["cuisine"] = df["cuisine"].fillna("Unknown")
            df["diet"] = df["diet"].str.lower()
            df["meal_time"] = df["meal_time"].str.title()
            
            # Add computed features
            df['is_quick'] = df['cook_time'] <= 15
            df['is_comfort'] = df['description'].str.lower().str.contains('comfort|cozy|warm|sooth', na=False)
            df['is_healthy'] = df['description'].str.lower().str.contains('fresh|light|healthy|clean', na=False)
            
            return df
        except FileNotFoundError:
            st.error(f"Recipe file not found at {PATHS['data']}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error loading recipes: {str(e)}")
            return pd.DataFrame()
    
    def save_embeddings(self, embeddings, recipe_ids):
        """Save embeddings to cache"""
        if not CACHE_CONFIG['enable_data_cache']:
            return
            
        cache_path = self.cache_dir / "recipe_embeddings.pkl"
        
        cache_data = {
            'embeddings': embeddings,
            'recipe_ids': recipe_ids,
            'timestamp': pd.Timestamp.now()
        }
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            st.warning(f"Could not save embeddings cache: {str(e)}")
    
    def load_embeddings(self, recipe_ids):
        """Load embeddings from cache if available and valid"""
        if not CACHE_CONFIG['enable_data_cache']:
            return None
            
        cache_path = self.cache_dir / "recipe_embeddings.pkl"
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Check if cache is still valid
            cache_age = (pd.Timestamp.now() - cache_data['timestamp']).total_seconds()
            if cache_age > CACHE_CONFIG['cache_ttl']:
                return None
            
            # Check if recipe IDs match
            if not np.array_equal(cache_data['recipe_ids'], recipe_ids):
                return None
            
            return cache_data['embeddings']
            
        except Exception as e:
            st.warning(f"Could not load embeddings cache: {str(e)}")
            return None
    
    def get_recipe_stats(self, df):
        """Get statistics about the recipe dataset"""
        if df.empty:
            return {}
        
        stats = {
            'total_recipes': len(df),
            'cuisines': df['cuisine'].value_counts().to_dict(),
            'diets': df['diet'].value_counts().to_dict(),
            'meal_times': df['meal_time'].value_counts().to_dict(),
            'avg_cook_time': df['cook_time'].mean(),
            'cook_time_range': (df['cook_time'].min(), df['cook_time'].max()),
            'quick_recipes': df['is_quick'].sum(),
            'comfort_recipes': df['is_comfort'].sum(),
            'healthy_recipes': df['is_healthy'].sum()
        }
        
        return stats
    
    def validate_recipe_data(self, df):
        """Validate recipe data integrity"""
        issues = []
        
        if df.empty:
            issues.append("Dataset is empty")
            return issues
        
        required_columns = ['title', 'description', 'diet', 'meal_time', 'cook_time', 'cuisine']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Missing columns: {missing_columns}")
        
        # Check for missing values in critical columns
        for col in ['title', 'meal_time', 'cook_time']:
            if col in df.columns and df[col].isnull().any():
                issues.append(f"Missing values in {col}")
        
        # Check cook_time validity
        if 'cook_time' in df.columns:
            invalid_times = df[(df['cook_time'] <= 0) | (df['cook_time'] > 300)]
            if not invalid_times.empty:
                issues.append(f"Invalid cook times: {len(invalid_times)} recipes")
        
        # Check for duplicate titles
        if 'title' in df.columns:
            duplicates = df['title'].duplicated().sum()
            if duplicates > 0:
                issues.append(f"Duplicate recipe titles: {duplicates}")
        
        return issues

# Global data loader instance
data_loader = DataLoader()