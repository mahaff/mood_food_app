"""Configuration settings for Mood Food Recommender"""

# App Settings
APP_TITLE = "🍽️ Mood Food Recommender"
APP_ICON = "🍽️"
MAX_RECOMMENDATIONS = 3
MAX_SAME_CUISINE = 2

# ML Settings
SIMILARITY_THRESHOLD = 0.1  # Minimum similarity score to show
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# Embedding weights for enhanced mode
EMBEDDING_WEIGHTS = {
    'text': 0.7,        # Primary weight on description
    'cuisine': 0.2,     # Cuisine feature weight
    'time': 0.1,        # Time-of-day weight
    'duration': 0.1     # Cooking duration weight
}

# User preference learning rates
LEARNING_RATES = {
    'cuisine_boost': 0.1,    # How much to boost liked cuisines
    'feedback_decay': 0.95,  # How much old feedback decays over time
    'max_history': 50        # Maximum items to keep in history
}

# Visualization settings
VIZ_CONFIG = {
    'max_recipes_radar': 5,
    'pca_components': 2,
    'plot_height': 500,
    'plot_width': 700
}

# Mood analysis settings
MOOD_CONFIG = {
    'max_tags': 5,
    'sentiment_thresholds': {
        'very_negative': -0.6,
        'negative': -0.3,
        'neutral': 0.3,
        'positive': 0.6
    },
    'intensity_boost': {
        'high': 1.5,
        'medium': 1.2,
        'low': 1.0
    }
}

# Cache settings
CACHE_CONFIG = {
    'embedding_cache_size': 100,
    'enable_data_cache': True,
    'cache_ttl': 3600  # 1 hour
}

# File paths
PATHS = {
    'data': 'data/recipes.csv',
    'embeddings_cache': 'cache/recipe_embeddings.pkl',
}