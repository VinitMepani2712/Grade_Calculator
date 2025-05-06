import pandas as pd

def weighted_score(raw, maximum, weight):
    return (raw / maximum) * weight if maximum else 0

# Read the CSV
df = pd.read_csv('grades.csv')

# Define weight for each category
weights = {
    'HW First Half': 40,
    'Quiz First Half': 60,
    'Midterm I': 90,
    'HW Second Half': 50,
    'Quiz Second Half': 60,
    'Midterm II': 90,
    'Project': 30,
    'Final': 180,
    'Extra Credit': 40,
}

categories = list(weights.keys())

# Calculate and print scores per student
for _, row in df.iterrows():
    name = row['Name']
    total = 0
    print(f"\n--- {name}'s Score Breakdown ---")
    
    for category in categories:
        raw_col = f"{category}_raw"
        max_col = f"{category}_maximum"
        
        raw = row[raw_col]
        maximum = row[max_col]
        weight = weights[category]
        
        pts = weighted_score(raw, maximum, weight)
        total += pts
        print(f"{category}: {pts:.2f} pts")
    
    print(f"\nTotal out of 600: {total:.2f} pts")
    print(f"Overall %: {total / 600 * 100:.2f}%")
