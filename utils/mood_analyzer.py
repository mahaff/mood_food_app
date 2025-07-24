import re
from textblob import TextBlob

class MoodAnalyzer:
    """Analyzes user mood text to extract emotional keywords and sentiment"""
    
    def __init__(self):
        self.emotion_keywords = {
            'stress': ['stressed', 'overwhelmed', 'anxious', 'tense', 'pressure', 'frazzled', 'hectic'],
            'comfort': ['sad', 'lonely', 'homesick', 'tired', 'exhausted', 'down', 'blue', 'melancholy'],
            'energy': ['energetic', 'excited', 'happy', 'motivated', 'pumped', 'enthusiastic', 'vibrant'],
            'calm': ['peaceful', 'relaxed', 'zen', 'meditative', 'serene', 'tranquil', 'chill'],
            'social': ['celebratory', 'party', 'friends', 'family', 'gathering', 'festive'],
            'indulgent': ['craving', 'treat', 'indulgent', 'guilty pleasure', 'comfort food'],
            'healthy': ['fresh', 'light', 'clean', 'detox', 'healthy', 'nutritious'],
            'quick': ['rushed', 'hurry', 'quick', 'fast', 'busy', 'no time'],
            'cozy': ['cozy', 'warm', 'comforting', 'snuggled', 'homey', 'intimate']
        }
        
        # Intensity modifiers
        self.intensity_words = {
            'very': 1.5, 'extremely': 2.0, 'super': 1.7, 'really': 1.3,
            'quite': 1.2, 'pretty': 1.1, 'somewhat': 0.8, 'slightly': 0.7,
            'a bit': 0.8, 'a little': 0.7, 'totally': 1.8, 'completely': 2.0
        }
    
    def extract_mood_tags(self, mood_text):
        """Extract mood tags and sentiment from user input"""
        if not mood_text:
            return [], 0.0
            
        mood_text_lower = mood_text.lower()
        
        # Extract sentiment using TextBlob
        blob = TextBlob(mood_text)
        sentiment = blob.sentiment.polarity
        
        # Find matching emotion categories
        detected_tags = []
        tag_scores = {}
        
        for category, keywords in self.emotion_keywords.items():
            category_score = 0
            matches = 0
            
            for keyword in keywords:
                if keyword in mood_text_lower:
                    matches += 1
                    # Check for intensity modifiers before the keyword
                    intensity = self._get_keyword_intensity(mood_text_lower, keyword)
                    category_score += intensity
            
            if matches > 0:
                tag_scores[category] = category_score / max(matches, 1)  # Average intensity
                detected_tags.append(category)
        
        # Add sentiment-based tags
        if sentiment < -0.4:
            detected_tags.append('negative')
        elif sentiment > 0.4:
            detected_tags.append('positive')
        elif -0.2 <= sentiment <= 0.2:
            detected_tags.append('neutral')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in detected_tags:
            if tag not in seen:
                unique_tags.append(tag)
                seen.add(tag)
        
        return unique_tags[:5], sentiment  # Limit to top 5 tags
    
    def _get_keyword_intensity(self, text, keyword):
        """Check if there are intensity modifiers near the keyword"""
        # Find the position of the keyword
        keyword_pos = text.find(keyword)
        if keyword_pos == -1:
            return 1.0
        
        # Look for intensity modifiers in the 20 characters before the keyword
        before_text = text[max(0, keyword_pos-20):keyword_pos]
        
        intensity = 1.0
        for modifier, multiplier in self.intensity_words.items():
            if modifier in before_text:
                intensity = max(intensity, multiplier)  # Use the strongest modifier
        
        return intensity
    
    def get_mood_summary(self, mood_tags, sentiment):
        """Generate a human-readable mood summary"""
        if not mood_tags:
            return "Neutral mood"
        
        # Primary mood
        primary = mood_tags[0] if mood_tags else "neutral"
        
        # Sentiment description
        if sentiment > 0.3:
            sentiment_desc = "positive"
        elif sentiment < -0.3:
            sentiment_desc = "challenging" 
        else:
            sentiment_desc = "balanced"
        
        # Create summary
        if len(mood_tags) == 1:
            return f"Feeling {primary} with a {sentiment_desc} outlook"
        else:
            secondary = ", ".join(mood_tags[1:3])  # Up to 2 more tags
            return f"Primarily {primary}, also {secondary} - overall {sentiment_desc}"