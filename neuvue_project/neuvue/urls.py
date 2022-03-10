"""neuvue URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path, include
from django.contrib.auth.views import LogoutView

from workspace.views import (
    WorkspaceView,
    TaskView,
    IndexView,
    AuthView,
    InspectTaskView,
    LineageView,
    DownloadView,
    TokenView,
    SynapseView
    )
from preferences.views import PreferencesView
from dashboard.views import DashboardView

urlpatterns = [
    path('', IndexView.as_view(), name="index"),
    path('preferences/', PreferencesView.as_view(), name="preferences"),
    path('tasks/', TaskView.as_view(), name="tasks"),
    path('workspace/<str:namespace>', WorkspaceView.as_view(), name="workspace"),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('dashboard/', DashboardView.as_view(), name="dashboard"),
    path('dashboard/namespace/<str:namespace>/group/<str:group>', DashboardView.as_view(), name="dashboard"),
    path('auth_redirect.html',AuthView.as_view(),name='auth_redirect'),
    path('token/', TokenView.as_view(), name='token'),
    path('inspect/', InspectTaskView.as_view(), name="inspect"), 
    path('inspect/<str:task_id>', InspectTaskView.as_view(), name="inspect"),
    path('lineage/', LineageView.as_view(), name="lineage"), 
    path('lineage/<str:root_id>', LineageView.as_view(), name="lineage"),
    path('download/',DownloadView.as_view(), name="download"),
    path('synapse/', SynapseView.as_view(), name="synapse"), 
    path('synapse/<str:root_id>', SynapseView.as_view(), name="synapse")
]



