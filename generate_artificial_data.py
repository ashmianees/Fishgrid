import csv
import random
from datetime import datetime, timedelta

# Expanded list of product names
product_names = [
    'Neon Tetra', 'Guppy', 'Angelfish', 'Betta Fish', 'Goldfish',
    'Molly', 'Platy', 'Discus', 'Corydoras Catfish', 'Zebra Danio',
    'Clown Loach', 'Rainbow Shark', 'Otocinclus Catfish', 'Siamese Algae Eater', 'Cherry Barb',
    'Fish Food Flakes', 'Fish Food Pellets', 'Frozen Bloodworms', 'Algae Wafers', 'Brine Shrimp',
    'Aquarium Filter - Small', 'Aquarium Filter - Medium', 'Aquarium Filter - Large', 'Filter Cartridges', 'Bio Balls',
    'Water Conditioner', 'pH Adjuster', 'Ammonia Remover', 'Algae Control', 'Bacterial Supplement',
    'Live Aquarium Plants - Anubias', 'Live Aquarium Plants - Java Fern', 'Live Aquarium Plants - Amazon Sword', 'Artificial Plants', 'Aquarium Moss',
    'Fish Tank - 5 Gallon', 'Fish Tank - 10 Gallon', 'Fish Tank - 20 Gallon', 'Fish Tank - 50 Gallon', 'Betta Tank',
    'Aquarium Heater', 'Thermometer', 'Air Pump', 'Air Stone', 'Check Valve',
    'Gravel Substrate', 'Sand Substrate', 'Decorative Rocks', 'Driftwood', 'Ceramic Ornaments',
    'Fish Net', 'Algae Scrubber', 'Gravel Vacuum', 'Water Test Kit', 'Quarantine Tank',
    'LED Aquarium Light', 'Automatic Fish Feeder', 'Breeding Box', 'Aquarium Background', 'Aquarium Stand'
]

# Generate artificial data
data = []
start_date = datetime.now() - timedelta(days=365)  # Start from one year ago

for _ in range(5000):  # Generate 5000 sales records
    product = random.choice(product_names)
    price = round(random.uniform(5.0, 200.0), 2)
    quantity = random.randint(1, 20)
    sale_date = start_date + timedelta(days=random.randint(0, 365))
    
    data.append([product, price, quantity, sale_date.strftime('%Y-%m-%d')])

# Write data to CSV file
with open('artificial_sales_data.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Product', 'Price', 'Quantity', 'Date'])  # Header
    writer.writerows(data)

print("Artificial data has been generated and saved to 'artificial_sales_data.csv'")