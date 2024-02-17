"""
URL configuration for rough_notebook project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('note', views.index, name='index'),
    path('note/', views.index, name='index'),
    path('signup', views.signup_view, name='signup_view'),
    path('forgot-password', views.forgot_password_view, name='forgot_password_view'),
    path('new_note', views.new_note, name='new_note'),
    path('note/<created>', views.view_note, name='view_note'),
    path('note/<created>/share', views.share_note, name='share_note'),
    path('note/<created>/edit', views.edit_note, name='edit_note'),
    path('note/<created>/update', views.update_note, name='update_note'),
    path('note/<created>/delete', views.delete_note, name='delete_note'),
]
