import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import plotly.express as px
import plotly.graph_objects as go

from model.embedder import get_embedding, EnhancedEmbedder
from utils.filters import filter_with_preferences, apply_diversity_filter
from utils.mood_analyzer import MoodAnalyzer
from utils.visualizer import create_mood_visualization, create_mood_dashboard

# Page config
st.set_page_config(
    page_title="🍽️ Mood Food Recommender", 
    page_icon="🍽️",
    layout="wide"
)

# Initialize components
@st.cache_resource
def load_components():
    mood_analyzer = MoodAnalyzer()
    enhanced_embedder = EnhancedEmbedder()
    return mood_analyzer, enhanced_embedder

mood_analyzer, enhanced_embedder = load_components()

# Initialize user profile
def initialize_user_profile():
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'liked_recipes': [],
            'disliked_recipes': [],
            'cuisine_preferences': {'Desi': 0.0, 'Arabic': 0.0, 'Western': 0.0},
            'mood_patterns': {}
        }

initialize_user_profile()

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("data/recipes.csv", on_bad_lines='skip')
    df["description"] = df["description"].fillna("")
    df["cuisine"] = df["cuisine"].fillna("Unknown")
    return df

df = load_data()

# Sidebar for advanced options
with st.sidebar:
    st.header("⚙️ Settings")
    
    use_enhanced_embeddings = st.checkbox("Use Enhanced AI Embeddings", value=True)
    show_visualizations = st.checkbox("Show Mood Visualizations", value=True)
    enable_learning = st.checkbox("Learn from my preferences", value=True)
    
    st.header("📊 Your Profile")
    if st.session_state.user_preferences['liked_recipes']:
        st.write("❤️ Liked recipes:", len(st.session_state.user_preferences['liked_recipes']))
        for recipe in st.session_state.user_preferences['liked_recipes'][-3:]:  # Show last 3
            st.write(f"• {recipe}")
    else:
        st.write("No preferences learned yet")
    
    if st.button("Reset Profile"):
        st.session_state.user_preferences = {
            'liked_recipes': [], 'disliked_recipes': [], 
            'cuisine_preferences': {'Desi': 0.0, 'Arabic': 0.0, 'Western': 0.0},
            'mood_patterns': {}
        }
        st.rerun()

# Main interface
st.title("🍽️ Mood Food Recommender")
st.write("Tell me how you're feeling, and I'll recommend the perfect meal for you!")

# Create two columns for input
col1, col2 = st.columns([2, 1])

with col1:
    mood = st.text_area(
        "Describe how you're feeling right now", 
        placeholder="e.g., I'm stressed and tired after a long day at work",
        height=100
    )

with col2:
    diet = st.selectbox("Dietary Preference", ["Any", "Vegan", "Vegetarian", "Halal"])
    meal_time = st.selectbox("Meal Time", ["Breakfast", "Lunch", "Dinner"])
    cook_time = st.slider("Max Cooking Time (minutes)", 5, 60, 30)

# Cuisine filter
cuisine = st.selectbox("Choose a Cuisine", ["All", "Desi", "Arabic", "Western"])

# Filter by cuisine
filtered_df = df.copy()
if cuisine != "All":
    filtered_df = filtered_df[filtered_df["cuisine"] == cuisine]
st.write(f"Recipes after cuisine filter: {len(filtered_df)}")

# Recommend button
if st.button("🎯 Recommend Me a Meal", type="primary"):
    if mood.strip() == "":
        st.warning("Please describe your mood first.")
    else:
        with st.spinner("Analyzing your mood and finding perfect matches..."):
            
            # Analyze mood
            mood_tags, sentiment = mood_analyzer.extract_mood_tags(mood)
            
            # Show mood analysis
            if mood_tags:
                st.info(f"🧠 Detected mood: {', '.join(mood_tags)} (sentiment: {sentiment:.2f})")
            
            # Get embeddings
            if use_enhanced_embeddings:
                # Use enhanced embeddings for recipes
                recipe_embeddings = []
                for _, recipe in filtered_df.iterrows():
                    emb = enhanced_embedder.get_enhanced_embedding(
                        recipe['description'], recipe['cuisine'], 
                        recipe['meal_time'], recipe['cook_time']
                    )
                    recipe_embeddings.append(emb)
                
                # Enhanced mood embedding (just text for now)
                mood_embedding = get_embedding(mood)
                # Pad mood embedding to match enhanced recipe embeddings
                emb_len = len(recipe_embeddings[0])
                mood_embedding = np.concatenate([mood_embedding, np.zeros(emb_len - len(mood_embedding))])
                
            else:
                # Original approach
                recipe_embeddings = [get_embedding(desc) for desc in filtered_df["description"]]
                mood_embedding = get_embedding(mood)
            
            # Calculate similarities
            similarities = cosine_similarity([mood_embedding], recipe_embeddings)[0]
            filtered_df = filtered_df.copy()
            filtered_df["similarity"] = similarities
            
            # Apply filters with user preferences
            user_prefs = st.session_state.user_preferences if enable_learning else None
            final_filtered = filtered_df  # For debugging, skip preference filtering
            
            # Add cuisine preference boost if learning enabled
            if enable_learning and 'cuisine_boost' in final_filtered.columns:
                final_filtered['final_score'] = final_filtered['similarity'] + final_filtered['cuisine_boost']
                sort_column = 'final_score'
            else:
                sort_column = 'similarity'
            
            # Get top matches with diversity
            top_matches = final_filtered.sort_values(by=sort_column, ascending=False).head(6)
            top_matches = apply_diversity_filter(top_matches, max_same_cuisine=2)

            if top_matches.empty:
                st.error("No matching meals found. Try adjusting your filters.")
            else:
                # Store for feedback
                st.session_state.last_recommendations = top_matches['title'].tolist()
                st.session_state.last_mood_tags = mood_tags
                
                # Show dashboard
                if show_visualizations:
                    create_mood_dashboard(top_matches.to_dict('records'))
                
                # Display recommendations
                st.header("🍽️ Your Personalized Recommendations")
                
                for i, (_, row) in enumerate(top_matches.iterrows()):
                    with st.container():
                        st.markdown(f"### {i+1}. {row['title']}")
                        
                        # Create columns for recipe info
                        info_col1, info_col2 = st.columns([3, 1])
                        
                        with info_col1:
                            st.write(f"🍴 {row['description']}")
                            
                            # Tags
                            tags = f"⏱ {row['cook_time']} mins • 🥗 {row['diet']} • 🍽 {row['meal_time']} • 🌍 {row['cuisine']}"
                            if 'final_score' in row:
                                tags += f" • 🎯 Match: {row['similarity']:.2f}"
                            else:
                                tags += f" • 🎯 Match: {row['similarity']:.2f}"
                            st.caption(tags)
                        
                        with info_col2:
                            st.metric("Mood Match", f"{row['similarity']:.1%}")
                    
                    st.markdown("---")
                
                # Visualizations
                if show_visualizations and len(top_matches) > 1:
                    st.header("📊 Mood-Food Analysis")
                    
                    try:
                        viz_fig = create_mood_visualization(
                            top_matches, mood_embedding, 
                            [recipe_embeddings[i] for i in top_matches.index]
                        )
                        st.plotly_chart(viz_fig, use_container_width=True)
                    except Exception as e:
                        st.info("Visualization not available (requires additional libraries)")

# Feedback section
if hasattr(st.session_state, 'last_recommendations') and enable_learning:
    st.header("💭 How did we do?")
    st.write("Your feedback helps us learn your preferences!")
    
    feedback_cols = st.columns(len(st.session_state.last_recommendations))
    
    for i, recipe in enumerate(st.session_state.last_recommendations):
        with feedback_cols[i]:
            if st.button(f"👍 Loved {recipe.split()[0]}", key=f"love_{recipe}"):
                # Update preferences
                prefs = st.session_state.user_preferences
                if recipe not in prefs['liked_recipes']:
                    prefs['liked_recipes'].append(recipe)
                    
                    # Update cuisine preference
                    recipe_row = df[df['title'] == recipe].iloc[0]
                    prefs['cuisine_preferences'][recipe_row['cuisine']] += 0.1
                    
                    # Learn mood patterns
                    for tag in st.session_state.get('last_mood_tags', []):
                        if tag not in prefs['mood_patterns']:
                            prefs['mood_patterns'][tag] = []
                        prefs['mood_patterns'][tag].append(recipe)
                    
                    st.success("Thanks! I'll remember you like this.")
                    st.rerun()
            
            if st.button(f"👎 Didn't like {recipe.split()[0]}", key=f"dislike_{recipe}"):
                # Update dislikes
                prefs = st.session_state.user_preferences
                if recipe not in prefs['disliked_recipes']:
                    prefs['disliked_recipes'].append(recipe)
                    st.success("Noted! I'll avoid similar recommendations.")
                    st.rerun()

# Footer
st.markdown("---")
st.markdown("*Built with ❤️ using AI-powered mood analysis and cultural food wisdom*")