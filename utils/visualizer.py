import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def create_mood_visualization(df, mood_embedding, recipe_embeddings):
    """Create an interactive visualization of mood-recipe similarity"""
    try:
        # Simple 2D projection using PCA (fallback if UMAP not available)
        from sklearn.decomposition import PCA
        
        # Ensure all embeddings have same dimension
        min_dim = min(len(mood_embedding), min(len(emb) for emb in recipe_embeddings))
        mood_emb_truncated = mood_embedding[:min_dim]
        recipe_embs_truncated = [emb[:min_dim] for emb in recipe_embeddings]
        
        all_embeddings = np.vstack([mood_emb_truncated.reshape(1, -1)] + recipe_embs_truncated)
        
        # Reduce to 2D
        reducer = PCA(n_components=2, random_state=42)
        reduced = reducer.fit_transform(all_embeddings)
        
        # Create the plot data
        plot_data = []
        
        # Add recipes
        for i, (_, recipe) in enumerate(df.iterrows()):
            plot_data.append({
                'x': reduced[i+1, 0],
                'y': reduced[i+1, 1],
                'name': recipe['title'],
                'cuisine': recipe['cuisine'],
                'similarity': recipe['similarity'],
                'cook_time': recipe['cook_time'],
                'type': 'Recipe'
            })
        
        # Convert to DataFrame
        plot_df = pd.DataFrame(plot_data)
        
        # Create scatter plot
        fig = px.scatter(
            plot_df,
            x='x', y='y',
            color='cuisine',
            size='similarity',
            hover_data=['name', 'cook_time'],
            title="Recipe-Mood Similarity Space",
            labels={'x': 'Dimension 1', 'y': 'Dimension 2'}
        )
        
        # Add mood point
        fig.add_scatter(
            x=[reduced[0, 0]], 
            y=[reduced[0, 1]], 
            mode='markers',
            marker=dict(symbol='star', size=20, color='red'),
            name='Your Mood',
            showlegend=True
        )
        
        # Update layout
        fig.update_layout(
            width=700,
            height=500,
            showlegend=True
        )
        
        return fig
        
    except ImportError:
        # Fallback: simple similarity bar chart
        fig = px.bar(
            df.head(5),
            x='similarity',
            y='title',
            orientation='h',
            color='cuisine',
            title="Top Recipe Matches for Your Mood"
        )
        
        fig.update_layout(
            width=700,
            height=400,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig
    
    except Exception as e:
        st.error(f"Visualization error: {str(e)}")
        return None

def create_mood_dashboard(recommendations):
    """Create a dashboard showing recommendation metrics"""
    if not recommendations:
        return
    
    # Calculate metrics
    avg_cook_time = np.mean([r['cook_time'] for r in recommendations])
    avg_similarity = np.mean([r['similarity'] for r in recommendations])
    cuisines = [r['cuisine'] for r in recommendations]
    dominant_cuisine = max(set(cuisines), key=cuisines.count) if cuisines else "Mixed"
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Cook Time", f"{avg_cook_time:.0f} min")
    
    with col2:
        st.metric("Mood Match", f"{avg_similarity:.1%}")
    
    with col3:
        st.metric("Recipes Found", len(recommendations))
    
    with col4:
        st.metric("Primary Cuisine", dominant_cuisine)

def create_cuisine_distribution_chart(recommendations):
    """Create a pie chart showing cuisine distribution"""
    if not recommendations:
        return None
    
    cuisines = [r['cuisine'] for r in recommendations]
    cuisine_counts = pd.Series(cuisines).value_counts()
    
    fig = px.pie(
        values=cuisine_counts.values,
        names=cuisine_counts.index,
        title="Cuisine Distribution in Recommendations"
    )
    
    return fig

def create_cooking_time_chart(recommendations):
    """Create a chart showing cooking time distribution"""
    if not recommendations:
        return None
    
    cook_times = [r['cook_time'] for r in recommendations]
    titles = [r['title'] for r in recommendations]
    
    fig = px.bar(
        x=titles,
        y=cook_times,
        title="Cooking Time by Recipe",
        labels={'x': 'Recipe', 'y': 'Cook Time (minutes)'}
    )
    
    fig.update_xaxis(tickangle=45)
    
    return fig

def create_similarity_radar_chart(recommendations, max_recipes=5):
    """Create a radar chart comparing recipe similarities"""
    if not recommendations:
        return None
    
    # Take top recipes
    top_recipes = recommendations[:max_recipes]
    
    # Create radar chart data
    categories = ['Mood Match', 'Quick to Make', 'Comfort Level']
    
    fig = go.Figure()
    
    for i, recipe in enumerate(top_recipes):
        # Calculate scores (normalize to 0-1)
        similarity = recipe.get('similarity', 0)
        quick_score = 1 - (recipe.get('cook_time', 30) / 60)  # Inverse of cook time
        comfort_score = 0.8 if 'comfort' in recipe.get('description', '').lower() else 0.5
        
        values = [similarity, quick_score, comfort_score]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=recipe['title'][:20] + ("..." if len(recipe['title']) > 20 else "")
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=True,
        title="Recipe Comparison Radar"
    )
    
    return fig