"""mrgol URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
import debug_toolbar
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from rest_framework.documentation import include_docs_urls



urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('users/', include('users.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('payment/', include('payment.urls')),
    path('__debug__/', include(debug_toolbar.urls)),
    path('doc/', include_docs_urls(title='loooool', description='visualize database: /static/main/mrgol_visualized.png/')),
    prefix_default_language=False,
)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

