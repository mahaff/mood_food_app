import pandas as pd
import numpy as np

def filter_recipes(df, diet, meal_time, cook_time):
    """Original filtering function"""
    filtered = df.copy()

    if diet != "Any":
        filtered = filtered[filtered["diet"].str.lower() == diet.lower()]

    filtered = filtered[filtered["meal_time"].str.lower() == meal_time.lower()]
    filtered = filtered[filtered["cook_time"] <= cook_time]
    return filtered

def filter_with_preferences(df, diet, meal_time, cook_time, user_preferences=None):
    """Enhanced filtering with user preferences"""
    # Apply basic filters
    filtered = filter_recipes(df, diet, meal_time, cook_time)
    
    if user_preferences is None:
        return filtered
    
    # Remove disliked recipes
    if user_preferences.get('disliked_recipes'):
        filtered = filtered[~filtered['title'].isin(user_preferences['disliked_recipes'])]
    
    # Boost preferred cuisines
    if user_preferences.get('cuisine_preferences'):
        cuisine_prefs = user_preferences['cuisine_preferences']
        filtered = filtered.copy()
        filtered['cuisine_boost'] = filtered['cuisine'].map(cuisine_prefs).fillna(0)
    else:
        filtered['cuisine_boost'] = 0
    
    return filtered

def apply_diversity_filter(recommendations, max_same_cuisine=2):
    """Ensure diversity in recommendations by limiting same cuisine"""
    if len(recommendations) <= max_same_cuisine:
        return recommendations
    
    diverse_recs = []
    cuisine_count = {}
    
    for _, recipe in recommendations.iterrows():
        cuisine = recipe['cuisine']
        count = cuisine_count.get(cuisine, 0)
        
        if count < max_same_cuisine:
            diverse_recs.append(recipe)
            cuisine_count[cuisine] = count + 1
            
        if len(diverse_recs) >= 3:  # Limit to top 3
            break
    
    return pd.DataFrame(diverse_recs)