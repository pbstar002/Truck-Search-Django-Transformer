import csv
import os
from django.conf import settings
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image
import torchvision.transforms as transforms
import timm
import numpy as np

# Load pre-trained Vision Transformer
model_name = 'vit_base_patch16_224'
model = timm.create_model(model_name, pretrained=True)
model.eval()
#source /home/truckpartsasia/virtualenv/TruckImageSearch/3.10/bin/activate && cd /home/truckpartsasia/TruckImageSearch
# Prepare the image transformation
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def get_categories_from_csv():
    categories = []

    with open('categories.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            categories.append(row[0])  # Assuming categories are in the first column

    return categories

def add_category_to_csv(category):
    with open('categories.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if category == row[0]:
                return False  # Category already exists

    # If not, add the category
    with open('categories.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([category])

    return True 

def remove_category_from_csv(category):
    # read the CSV, filter out the category and then write it back
    with open('categories.csv', 'r') as f:
        rows = [line.strip() for line in f.readlines() if line.strip() != category]

    with open('categories.csv', 'w') as f:
        for row in rows:
            f.write(row + "\n")

    return True

def process_image(img_path):
    img = Image.open(img_path).convert('L')  # Convert to grayscale
    img = img.resize((224, 224))  # Resize the image
    img = np.array(img)  # Convert to numpy array
    img = img / 255.0  # Normalize to [0, 1]
    img = np.repeat(img[..., np.newaxis], 3, -1)  # Duplicate grayscale image to 3 channels
    img = transform(img)  # Apply the transformation
    return img

def extract_features(model, img):
    img = img.float()  # Convert input tensor to float
    img = img.unsqueeze(0)  # Add batch dimension
    features = model.forward_features(img)  # Extract features using Vision Transformer
    return features.flatten().detach().numpy()


# Function for similarity calculation
def find_similar_images(query_img_path, img_features):
    print(query_img_path)
    query_img = process_image(query_img_path)
    query_features = extract_features(model, query_img)

    similarities = {}
    for img_path, features in img_features.items():
        similarity = cosine_similarity([query_features], [features])
        similarities[img_path] = similarity[0][0]
    
    # Sort images by similarity score
    sorted_similarities = sorted(similarities.items(), key=lambda item: item[1], reverse=True)
    
    return sorted_similarities

def fn_search(model_name, query_image):
    model_name = "models\\"  +  model_name

    model_path = os.path.join(settings.BASE_DIR, model_name)
    # Load features from file
    with open(model_path, 'rb') as f:
        img_features = pickle.load(f)

    similar_images = find_similar_images(query_image, img_features)
    return similar_images[:10]