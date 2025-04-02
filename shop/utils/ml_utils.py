import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..models import Order, Product
import random
from scipy import stats
import numpy as np
from sklearn.metrics import silhouette_score

class RecommendationSystem:
    def __init__(self):
        try:
            self.product_popularity = joblib.load('product_popularity.joblib')
            self.vectorizer = joblib.load('vectorizer.joblib')
            self.cosine_sim = joblib.load('cosine_sim.joblib')
        except FileNotFoundError:
            print("Model files not found. Initializing with empty data.")
            self.product_popularity = pd.DataFrame(columns=['Product', 'Quantity', 'PopularityScore'])
            self.vectorizer = TfidfVectorizer()
            self.cosine_sim = None

    def update_model(self, new_orders):
        if not new_orders:
            print("No new orders to process.")
            return

        # Convert new orders to DataFrame
        new_df = pd.DataFrame(new_orders)
        
        # Update product popularity
        new_popularity = new_df.groupby('product_name')['quantity'].sum().reset_index()
        new_popularity.columns = ['Product', 'Quantity']
        
        self.product_popularity = pd.concat([self.product_popularity, new_popularity]).groupby('Product')['Quantity'].sum().reset_index()
        
        # Calculate relative popularity score (1-100 scale)
        max_quantity = self.product_popularity['Quantity'].max()
        min_quantity = self.product_popularity['Quantity'].min()
        
        if max_quantity == min_quantity:
            self.product_popularity['PopularityScore'] = 100
        else:
            self.product_popularity['PopularityScore'] = ((self.product_popularity['Quantity'] - min_quantity) / (max_quantity - min_quantity) * 99 + 1).round().astype(int)
        
        # Update TF-IDF matrix and cosine similarity
        if len(self.product_popularity) > 1:
            tfidf_matrix = self.vectorizer.fit_transform(self.product_popularity['Product'])
            self.cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        else:
            print("Not enough data to compute cosine similarity.")
            self.cosine_sim = None
        
        # Save updated model
        joblib.dump(self.product_popularity, 'product_popularity.joblib')
        joblib.dump(self.vectorizer, 'vectorizer.joblib')
        if self.cosine_sim is not None:
            joblib.dump(self.cosine_sim, 'cosine_sim.joblib')

    def get_recommendations(self, product_name, n=5):
        if self.cosine_sim is None or len(self.product_popularity) < 2:
            print("Not enough data for recommendations.")
            return []

        # Get index of the product
        if product_name not in self.product_popularity['Product'].values:
            print(f"Product '{product_name}' not found in the data.")
            return []

        idx = self.product_popularity[self.product_popularity['Product'] == product_name].index[0]
        
        # Get similarity scores
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:n+1]  # Exclude the product itself
        
        # Get product indices
        product_indices = [i[0] for i in sim_scores]
        
        # Return recommended products with their popularity scores
        recommendations = self.product_popularity.iloc[product_indices]
        return recommendations[['Product', 'PopularityScore']].to_dict('records')

recommendation_system = RecommendationSystem()

def get_product_recommendations(shop_id, offset=0, limit=12):
    current_shop_products = Product.objects.filter(shop_id=shop_id).values_list('product_name', flat=True)
    all_products = recommendation_system.product_popularity['Product'].tolist()
    products_to_recommend = list(set(all_products) - set(current_shop_products))
    
    if not products_to_recommend:
        return []
    
    recommendations = []
    for product in products_to_recommend:
        recommendations.extend(recommendation_system.get_recommendations(product))
    
    # Remove duplicates and sort by popularity
    unique_recommendations = []
    seen = set()
    for r in recommendations:
        if r['Product'] not in seen and r['Product'] not in current_shop_products:
            unique_recommendations.append(r)
            seen.add(r['Product'])
    
    unique_recommendations.sort(key=lambda x: x['PopularityScore'], reverse=True)
    return unique_recommendations[offset:offset+limit]

def update_model_with_new_orders():
    # Fetch new orders since last update
    last_update = Order.objects.latest('order_date').order_date if Order.objects.exists() else None
    new_orders = Order.objects.filter(order_date__gt=last_update) if last_update else Order.objects.all()
    
    print("Debug: Number of new orders:", new_orders.count())
    
    # Prepare data for model update
    order_data = []
    for order in new_orders:
        for order_detail in order.order_details.all():
            order_data.append({
                'product_name': order_detail.product.product_name,
                'quantity': order_detail.quantity
            })
    
    print("Debug: order_data:", order_data)
    
    # Update the model
    recommendation_system.update_model(order_data)

# Initialize the model with existing data
def initialize_model():
    from shop.models import Order, OrderDetails
    print("\n=== Initializing Recommendation Model ===")
    
    # Load existing orders
    all_orders = Order.objects.all()
    order_data = []
    for order in all_orders:
        for order_detail in order.order_details.all():
            order_data.append({
                'product_name': order_detail.product.product_name,
                'quantity': order_detail.quantity
            })
    
    # Update the model
    recommendation_system.update_model(order_data)
    
    print("\n=== Model Accuracy Metrics ===")
    
    try:
        # Convert order data to numpy arrays for statistical analysis
        df = pd.DataFrame(order_data)
        purchase_matrix = df.pivot_table(
            index='product_name', 
            values='quantity',
            aggfunc='sum',
            fill_value=0
        ).values
        
        # 1. Chi-square test for independence
        if purchase_matrix.size > 1:
            chi2, p_value = stats.chisquare(purchase_matrix)
            chi2_score = np.mean(chi2)
            
            # 2. Calculate Pearson correlation between predicted and actual purchases
            if recommendation_system.cosine_sim is not None:
                correlation_matrix = np.corrcoef(recommendation_system.cosine_sim)
                correlation_score = np.mean(np.abs(correlation_matrix))
                
                # 3. Calculate silhouette score for clustering quality
                if len(purchase_matrix) > 1:
                    try:
                        silhouette_avg = silhouette_score(
                            purchase_matrix.reshape(-1, 1), 
                            recommendation_system.product_popularity['PopularityScore']
                        )
                    except:
                        silhouette_avg = 0
                
                # 4. Calculate R-squared score
                total_variance = np.var(purchase_matrix)
                predicted_variance = np.var(recommendation_system.cosine_sim)
                r_squared = 1 - (predicted_variance / total_variance) if total_variance != 0 else 0
                
                print("\nStatistical Accuracy Metrics:")
                print(f"Chi-square score: {chi2_score:.4f} (p-value: {p_value.mean():.4f})")
                print(f"Correlation score: {correlation_score:.4f}")
                print(f"Silhouette score: {silhouette_avg:.4f}")
                print(f"R-squared score: {r_squared:.4f}")
                
                # Calculate overall model accuracy
                weights = [0.3, 0.3, 0.2, 0.2]  # Weights for each metric
                metrics = [
                    min(1, chi2_score/1000),  # Normalized chi-square
                    correlation_score,
                    max(0, silhouette_avg),
                    r_squared
                ]
                
                overall_accuracy = sum(w * m for w, m in zip(weights, metrics))
                print(f"\nOverall Model Accuracy: {overall_accuracy:.4f} ({overall_accuracy*100:.2f}%)")
                
                # Additional model statistics
                print("\nModel Statistics:")
                print(f"Total products: {len(recommendation_system.product_popularity)}")
                print(f"Average popularity score: {recommendation_system.product_popularity['PopularityScore'].mean():.2f}")
                print(f"Recommendation matrix shape: {recommendation_system.cosine_sim.shape}")
            else:
                print("\nNot enough data for correlation analysis")
        else:
            print("\nNot enough data for statistical analysis")
            
    except Exception as e:
        print(f"Error calculating accuracy metrics: {str(e)}")
    
    print("\n=== Model Initialization Complete ===")

# Call this function when the server starts
# initialize_model()  # Remove or comment out this line

