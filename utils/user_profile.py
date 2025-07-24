import json
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
from config import LEARNING_RATES

class UserProfileManager:
    """Manages user preferences and learning"""
    
    def __init__(self):
        self.profile_path = Path("cache/user_profiles.json")
        self.profile_path.parent.mkdir(exist_ok=True)
        
    def initialize_profile(self):
        """Initialize user profile in session state"""
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {
                'liked_recipes': [],
                'disliked_recipes': [],
                'cuisine_preferences': {'Desi': 0.0, 'Arabic': 0.0, 'Western': 0.0},
                'mood_patterns': {},
                'feedback_history': [],
                'creation_date': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
    
    def add_feedback(self, recipe_title, rating, mood_tags, recipe_data):
        """Add user feedback and update preferences"""
        prefs = st.session_state.user_preferences
        
        # Create feedback record
        feedback = {
            'recipe_title': recipe_title,
            'rating': rating,
            'mood_tags': mood_tags,
            'timestamp': datetime.now().isoformat(),
            'cuisine': recipe_data.get('cuisine'),
            'meal_time': recipe_data.get('meal_time'),
            'cook_time': recipe_data.get('cook_time')
        }
        
        # Add to history
        prefs['feedback_history'].append(feedback)
        
        # Limit history size
        if len(prefs['feedback_history']) > LEARNING_RATES['max_history']:
            prefs['feedback_history'] = prefs['feedback_history'][-LEARNING_RATES['max_history']:]
        
        # Update preferences based on rating
        if rating >= 4:  # Positive feedback
            if recipe_title not in prefs['liked_recipes']:
                prefs['liked_recipes'].append(recipe_title)
            
            # Remove from dislikes if present
            if recipe_title in prefs['disliked_recipes']:
                prefs['disliked_recipes'].remove(recipe_title)
            
            # Update cuisine preference
            if recipe_data.get('cuisine') in prefs['cuisine_preferences']:
                current = prefs['cuisine_preferences'][recipe_data['cuisine']]
                prefs['cuisine_preferences'][recipe_data['cuisine']] = min(1.0, 
                    current + LEARNING_RATES['cuisine_boost'])
            
            # Learn mood patterns
            for tag in mood_tags:
                if tag not in prefs['mood_patterns']:
                    prefs['mood_patterns'][tag] = []
                if recipe_title not in prefs['mood_patterns'][tag]:
                    prefs['mood_patterns'][tag].append(recipe_title)
        
        elif rating <= 2:  # Negative feedback
            if recipe_title not in prefs['disliked_recipes']:
                prefs['disliked_recipes'].append(recipe_title)
            
            # Remove from likes if present
            if recipe_title in prefs['liked_recipes']:
                prefs['liked_recipes'].remove(recipe_title)
            
            # Slightly reduce cuisine preference
            if recipe_data.get('cuisine') in prefs['cuisine_preferences']:
                current = prefs['cuisine_preferences'][recipe_data['cuisine']]
                prefs['cuisine_preferences'][recipe_data['cuisine']] = max(-0.5,
                    current - LEARNING_RATES['cuisine_boost'] * 0.5)
        
        # Update timestamp
        prefs['last_updated'] = datetime.now().isoformat()
        
        # Auto-save profile
        self.save_profile()
    
    def get_personalized_boost(self, recipe_row):
        """Calculate personalized boost score for a recipe"""
        if 'user_preferences' not in st.session_state:
            return 0.0
        
        prefs = st.session_state.user_preferences
        boost = 0.0
        
        # Cuisine preference boost
        cuisine = recipe_row.get('cuisine')
        if cuisine in prefs['cuisine_preferences']:
            boost += prefs['cuisine_preferences'][cuisine] * 0.3
        
        # Liked recipes boost (similar recipes)
        if recipe_row.get('title') in prefs['liked_recipes']:
            boost += 0.5
        
        # Disliked recipes penalty
        if recipe_row.get('title') in prefs['disliked_recipes']:
            boost -= 1.0  # Strong penalty
        
        # Time-based decay for old feedback
        recent_feedback = self._get_recent_feedback(days=30)
        if recent_feedback:
            # Boost recipes similar to recently liked ones
            recent_likes = [f for f in recent_feedback if f['rating'] >= 4]
            for like in recent_likes:
                if (like.get('cuisine') == cuisine and 
                    like.get('meal_time') == recipe_row.get('meal_time')):
                    boost += 0.1
        
        return max(-1.0, min(1.0, boost))  # Clamp between -1 and 1
    
    def _get_recent_feedback(self, days=30):
        """Get feedback from recent days"""
        if 'user_preferences' not in st.session_state:
            return []
        
        prefs = st.session_state.user_preferences
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent = []
        for feedback in prefs.get('feedback_history', []):
            try:
                feedback_date = datetime.fromisoformat(feedback['timestamp'])
                if feedback_date > cutoff_date:
                    recent.append(feedback)
            except (KeyError, ValueError):
                continue
        
        return recent
    
    def get_profile_summary(self):
        """Get a summary of user preferences"""
        if 'user_preferences' not in st.session_state:
            return {"status": "No profile data"}
        
        prefs = st.session_state.user_preferences
        
        # Calculate favorite cuisine
        cuisine_prefs = prefs.get('cuisine_preferences', {})
        fav_cuisine = max(cuisine_prefs, key=cuisine_prefs.get) if cuisine_prefs else "None"
        
        # Get recent activity
        recent_feedback = self._get_recent_feedback(days=7)
        
        summary = {
            'total_feedback': len(prefs.get('feedback_history', [])),
            'liked_recipes': len(prefs.get('liked_recipes', [])),
            'disliked_recipes': len(prefs.get('disliked_recipes', [])),
            'favorite_cuisine': fav_cuisine,
            'cuisine_scores': cuisine_prefs,
            'recent_activity': len(recent_feedback),
            'mood_patterns': len(prefs.get('mood_patterns', {})),
            'profile_age_days': self._get_profile_age_days()
        }
        
        return summary
    
    def _get_profile_age_days(self):
        """Calculate how old the user profile is"""
        if 'user_preferences' not in st.session_state:
            return 0
        
        prefs = st.session_state.user_preferences
        try:
            creation_date = datetime.fromisoformat(prefs.get('creation_date', datetime.now().isoformat()))
            return (datetime.now() - creation_date).days
        except:
            return 0
    
    def reset_profile(self):
        """Reset user profile to default state"""
        if 'user_preferences' in st.session_state:
            del st.session_state.user_preferences
        self.initialize_profile()
        
        # Remove saved profile file
        if self.profile_path.exists():
            try:
                self.profile_path.unlink()
            except:
                pass
    
    def save_profile(self):
        """Save user profile to disk"""
        if 'user_preferences' not in st.session_state:
            return
        
        try:
            with open(self.profile_path, 'w') as f:
                json.dump(st.session_state.user_preferences, f, indent=2)
        except Exception as e:
            st.warning(f"Could not save user profile: {str(e)}")
    
    def load_profile(self):
        """Load user profile from disk"""
        if not self.profile_path.exists():
            return
        
        try:
            with open(self.profile_path, 'r') as f:
                saved_prefs = json.load(f)
            
            # Merge with current session state
            self.initialize_profile()
            st.session_state.user_preferences.update(saved_prefs)
            
        except Exception as e:
            st.warning(f"Could not load saved profile: {str(e)}")

# Global profile manager
profile_manager = UserProfileManager()