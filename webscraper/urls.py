from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('start_scraping/', views.start_scraping, name='start_scraping'),
    path('check_sitemap_status/', views.check_sitemap_status, name='check_sitemap_status'),
    path('download_sitemap/', views.download_sitemap, name='download_sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
