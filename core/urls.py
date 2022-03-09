from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.urls import include

# SWAGGER CONFIG
schema_view = get_schema_view(
    openapi.Info(
        title="Chat API",
        default_version="v1",
        description="Chat API",
        terms_of_service="",
        contact=openapi.Contact(email="a.khushnazarov@uic.group"),
        license=openapi.License(name="License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ws/chat/', include('chat.rest.urls', namespace='chat'))
]

if settings.DEBUG:
    urlpatterns += [
        path(
            "swagger/",
            schema_view.with_ui("swagger", cache_timeout=0),
            name="schema-swagger-ui",
        ),
    ]

# MEDIA URLS
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
