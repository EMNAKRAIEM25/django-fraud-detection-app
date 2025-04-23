from django.urls import path
from . import views

urlpatterns = [
    path('', views.projects, name="projects_home"),
    path('projects/', views.projects, name="projects"),
    path('projects/save/', views.save_form, name="save_form"),
    path('update_enregistrement/<int:id>/', views.update_enregistrement, name='update_enregistrement'),
    path('delete_enregistrement/<int:id>/', views.delete_enregistrement, name='delete_enregistrement'),

    path('create-project/', views.createProject, name="create-project"),

    path('update-project/<str:pk>/', views.updateProject, name="update-project"),
    path('delete-project/<str:pk>/', views.deleteProject, name="delete-project"),
    
    
]
