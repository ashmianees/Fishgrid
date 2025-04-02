import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib

def train_model(data_file):
    # Load data
    df = pd.read_csv(data_file)
    
    # Calculate product popularity
    product_popularity = df.groupby('Product')['Quantity'].sum().reset_index()
    product_popularity['PopularityScore'] = product_popularity['Quantity'] / product_popularity['Quantity'].sum()
    
    # Create TF-IDF matrix for product names
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(product_popularity['Product'])
    
    # Calculate cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # Save model artifacts
    joblib.dump(product_popularity, 'product_popularity.joblib')
    joblib.dump(vectorizer, 'vectorizer.joblib')
    joblib.dump(cosine_sim, 'cosine_sim.joblib')

    print("Model trained and saved successfully")

if __name__ == "__main__":
    train_model('artificial_sales_data.csv')