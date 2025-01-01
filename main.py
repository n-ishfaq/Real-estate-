from flask import Flask, render_template, request 
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os 
from PIL import Image
from pathlib import Path
import pathlib
# Flask app
app = Flask(__name__)

# Function to create similarity matrix
def create_similarity():
    # Load real estate dataset
    print("File Exists:", os.path.exists("socal2.csv"))
    data = pd.read_csv('socal2.csv',encoding='utf-8')  # Replace with your dataset filename
    
    # Combine features into a single string for each listing
    data['combined'] = (
        data['image_id'].astype(str) + ' ' +
        data['citi'].astype(str) + ' ' +
        data['bed'].astype(str) + ' ' +
        data['bath'].astype(str) + ' ' +
        data['sqft'].astype(str) + ' ' +
        data['price'].astype(str)
    )
    
    # Create a count matrix based on combined features
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(data['combined'])
    
    # Calculate cosine similarity matrix
    similarity = cosine_similarity(count_matrix)
    
    return data, similarity

# Recommendation function
def rcmd(property_id):
    try:
        data, similarity = create_similarity()
    except Exception as e:
        return f"Error: {e}"
    
    if property_id not in data['image_id'].values:
        return 'Sorry! The property ID is not in our database.'
    
    idx = data.loc[data['image_id'] == property_id].index[0]
    scores = list(enumerate(similarity[idx]))
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
    top_recommendations = sorted_scores[1:4]

    recommendations = []
    for i, score in top_recommendations:
        rec = {
            "image_id": data.iloc[i]['image_id'],
            "citi": data.iloc[i]['citi'],
            "bed": data.iloc[i]['bed'],
            "bath": data.iloc[i]['bath'],
            "sqft": data.iloc[i]['sqft'],
            "price": data.iloc[i]['price'],
            "similarity_score": round(score, 2),
        }
        recommendations.append(rec)
    
    image_dir = "socal_pics"
    if not os.path.exists(image_dir):
        return f"Error: Directory '{image_dir}' does not exist."
    
    file_list = os.listdir(image_dir)
    for rec in recommendations:
        image_id = str(rec['image_id'])
        matching_files = [f for f in file_list if image_id in f]
        if matching_files:
            rec['image_path'] = os.path.join(image_dir, matching_files[0])
        else:
            rec['image_path'] = None  # Handle missing images
    
    return recommendations

# Route: Home
@app.route("/")
@app.route("/home")
def home():
    data, _ = create_similarity()
    suggestions = data['citi'].unique()  # Cities for suggestions
    return render_template('home.html', suggestions=suggestions)

# Route: Recommendation
@app.route("/recommend", methods=["POST"])
def recommend():
    # Get property ID from user input
    property_id = int(request.form['property_id'])
    
    # Get recommendations
    recommendations = rcmd(property_id)
    
    if isinstance(recommendations, str):  # If error message
        return recommendations
    
    # Pass recommendations to template
    return render_template('recommend.html', recommendations=recommendations)

# Main
if __name__ == "__main__":
    app.run(debug=True)     