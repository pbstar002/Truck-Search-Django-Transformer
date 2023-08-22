from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.core.files.storage import default_storage
import os
from django.conf import settings
from django.core.files.base import ContentFile
from .utils import *
import json
from pathlib import Path

class HomeView(View):
    def get(self, request):
        categories = get_categories_from_csv()
        return render(request, "home.html", {'categories': categories})
    
class TrainView(View):
    def get(self, request):
        categories = get_categories_from_csv()
        return render(request, "train.html", {'categories': categories})

class SearchView(View):
    def post(self, request):
        image = request.FILES.get('image')
        category = request.POST.get('category')
        print(category)
        path = os.path.join(settings.MEDIA_ROOT, 'uploads', image.name)
        default_storage.save(path, ContentFile(image.read()))
        
        try:
            similar_images = fn_search(category+".pkl", path)
            # Convert float scores to strings
            similar_images_serializable = [(img, str(score)) for img, score in similar_images]
            print(similar_images_serializable)
            response_data = {
                "similar_images": similar_images_serializable
            }
            print(response_data)
            return JsonResponse(response_data)
        except Exception as e:
            print(e)  # To see the exception in the console
            response_data = {
                "similar_images": []
            }
            return JsonResponse(response_data)

class GetCategoryCountView(View):
    def get(self, request):
        base_path = os.path.join(settings.MEDIA_ROOT, 'ImageSearch', 'train_datasets')
        categories = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
        counts = {}
        for category in categories:
            count = len([f for f in os.listdir(os.path.join(base_path, category)) if os.path.isfile(os.path.join(base_path, category, f))])
            counts[category] = count
        return JsonResponse(counts)

class AddCategoryView(View):
    def post(self, request):
        data = json.loads(request.body)
        new_category = data.get('category', '')
        print(new_category)
        success = add_category_to_csv(new_category)

        if success:
            return JsonResponse({"success": True, "message": "Category added successfully"})
        else:
            return JsonResponse({"success": False, "message": "Failed to add category"}, status=400)
        
class DeleteCategoryView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            category_to_delete = data.get('category')
            if not category_to_delete:
                    return JsonResponse({'success': False, 'error': 'Category not provided'})
            success = remove_category_from_csv(category_to_delete)

            return JsonResponse({'success': success})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
class TrainImageView(View):
    def post(self, request):
        category = request.POST.get('categorySelect')
        upload_files = request.FILES.getlist('files')
        uploaded_images = []
        for upload_file in upload_files:
            path = os.path.join(settings.MEDIA_ROOT, 'ImageSearch', 'train_datasets', category, upload_file.name)
            os.makedirs(os.path.dirname(path), exist_ok=True)  # Create parent directories if they don't exist
                    # If file with same name already exists, delete it
            if default_storage.exists(path):
                default_storage.delete(path)
            default_storage.save(path, ContentFile(upload_file.read()))
            uploaded_images.append(path)

        img_features = {}
        model_path = os.path.join(settings.BASE_DIR, 'models', category+".pkl")
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                img_features = pickle.load(f)
        
        for img_path in uploaded_images:
            img = process_image(img_path)
            features = extract_features(model, img)
            rel_path = str(Path(img_path).relative_to(settings.BASE_DIR))
            img_features[rel_path] = features
        with open(model_path, 'wb') as f:
            pickle.dump(img_features, f)

        merged_model_file = os.path.join(settings.BASE_DIR, 'models', "All.pkl")
        all_features = {}
        if os.path.exists(merged_model_file):
            with open(merged_model_file, 'rb') as f:
                all_features = pickle.load(f)
        else:
            all_features = {}


        all_features.update(img_features)
        with open(merged_model_file, 'wb') as f:
            pickle.dump(all_features, f) 

        return JsonResponse({"message": "success"})