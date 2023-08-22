from django.urls import path
from .views import *

urlpatterns = [
    path("", HomeView.as_view()),
    path("train", TrainView.as_view()),
    path("api/search", SearchView.as_view()),
    path("api/add_category", AddCategoryView.as_view()),
    path("api/delete_category", DeleteCategoryView.as_view()),
    path("api/train_image", TrainImageView.as_view()),
    path("api/get_category_counts", GetCategoryCountView.as_view())
]
