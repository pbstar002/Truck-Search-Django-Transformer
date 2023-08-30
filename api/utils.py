import csv
import os
from django.conf import settings
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import faiss
import os
import pickle
from pathlib import Path
class ImageSearch:
    def __init__(self, dimension=2048):
        self.dimension = dimension
        print("Index Dimension:", dimension)  # Print the dimension for debugging
        self.index = faiss.IndexFlatL2(dimension)
        self.image_paths = []

        # Initialize pre-trained ResNet model + higher level layers
        self.model = models.resnet50(pretrained=True)

        # Remove final fully connected layer to get 2048 dimensional output
        modules = list(self.model.children())[:-2]
        self.model = torch.nn.Sequential(*modules)
        
        if torch.cuda.is_available():
            self.model = self.model.cuda()
        
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),

        ])
    def save_all_index(self):
        self.save_category_index("all")

    def load_all_index(self):
        if os.path.exists("all_faiss_index.pkl"):
            self.load_category_index("all")
        else:
            self.create_empty_index()

    def create_empty_index(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.image_paths = []

    def merge_category_into_all(self, category_name):
        self.load_all_index()
        category_searcher = ImageSearch()
        category_searcher.load_category_index(category_name)
        self.merge_with(category_searcher)
        self.save_all_index()

    def extract_features(self, image_path):
        image = Image.open(image_path).convert("RGB")
        tensor = self.transform(image).unsqueeze(0)
        if torch.cuda.is_available():
            tensor = tensor.cuda()
        with torch.no_grad():
            features = self.model(tensor)
        
        # Apply Global Average Pooling
        features = features.mean([2, 3])
        
        return features.cpu().numpy()

    def add_to_index(self, image_path):
        image_path = str(Path(image_path).relative_to(settings.BASE_DIR))
        feature = self.extract_features(image_path)
        # print("Feature Shape:", feature.shape)  # Print the shape for debugging
        self.index.add(feature)

        self.image_paths.append(image_path)

    def search(self, query_image_path, k=10):
        query_feature = self.extract_features(query_image_path)
        distances, indices = self.index.search(query_feature, k)

        results = [self.image_paths[idx] for idx in indices[0]]
        return results
    def save_category_index(self, category_name):
        index_path = f"{category_name}_faiss_index.pkl"
        image_paths_path = f"{category_name}_image_paths.pkl"
        faiss.write_index(self.index, index_path)
        with open(image_paths_path, 'wb') as f:
            pickle.dump(self.image_paths, f)

    def load_category_index(self, category_name):
        index_path = f"{category_name}_faiss_index.pkl"
        image_paths_path = f"{category_name}_image_paths.pkl"
        self.index = faiss.read_index(index_path)
        with open(image_paths_path, 'rb') as f:
            self.image_paths = pickle.load(f)   
    def merge_with(self, another_searcher):
        self.index.add(another_searcher.index.reconstruct_n(0, another_searcher.index.ntotal))
        self.image_paths.extend(another_searcher.image_paths)


def get_categories_from_csv():
    categories = []
    csv_path = os.path.join(settings.BASE_DIR, 'categories.csv')
    with open(csv_path, newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            categories.append(row[0])  # Assuming categories are in the first column

    return categories

def add_category_to_csv(category):
    csv_path = os.path.join(settings.BASE_DIR, 'categories.csv')
    with open(csv_path, 'r') as file:
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
