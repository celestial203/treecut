from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),  # Root URL redirects to login
    path('login/', views.login_view, name='login'),  # Keep this for explicit login URL
    path('homepage/', views.homepage, name='homepage'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cutting/', views.cutting, name='cutting'),
    path('cutting/<int:cutting_id>/view/', views.view_cutting, name='view_cutting'),
    path('cutting/<int:pk>/edit/', views.edit_cutting, name='edit_cutting'),
    path('cutting/<int:cutting_id>/record/add/', views.add_cutting_record, name='add_cutting_record'),
    path('wood/', views.wood, name='wood'),
    path('wood/records/', views.wood_records, name='wood_records'),
    path('wood/<int:pk>/view/', views.wood_detail, name='wood_detail'),
    path('wood/<int:pk>/edit/', views.edit_wood, name='edit_wood'),
    path('wood/<int:pk>/update/', views.update_wood, name='update_wood'),
    path('wood/<int:pk>/delete/', views.delete_wood, name='delete_wood'),
    path('lumber/', views.lumber, name='lumber'),
    path('edit_recordlumber/<int:pk>/', views.edit_recordlumber, name='edit_recordlumber'),
    path('search/', views.search, name='search'),
    path('chainsaw/', views.chainsaw, name='chainsaw'),
    path('chainsaw/record/', views.chainsaw_records, name='chainsaw_record'),
    path('chainsaw/<int:pk>/view/', views.view_chainsaw, name='view_chainsaw'),
    path('chainsaw/<int:pk>/renew/', views.renew_chainsaw, name='renew_chainsaw'),
    path('edit-chainsaw/<int:pk>/', views.edit_chainsaw, name='edit_chainsaw'),
    path('edit-wood/<int:pk>/', views.edit_wood, name='edit_wood'),
    path('profile/', views.profile, name='profile'),
    path('cutting/record/edit/<int:record_id>/', views.edit_cutting_record, name='edit_cutting_record'),
    path('cutting/records/', views.cutting_records, name='cutting_records'),
    path('cutting/volumes/', views.volumes, name='volumes'),
    path('check-permit-exists/', views.check_permit_exists, name='check-permit-exists'),
    path('cutting/volume-records/', views.volume_records_list, name='volume_records_list'),
    path('lumber/records/', views.lumber_records, name='lumber_records'),
    path('lumber/<int:pk>/details/', views.view_lumber_details, name='view_lumber_details'),
    path('calculate-volumes/', views.calculate_volumes, name='calculate_volumes'),
    path('edit-volume-record/<int:record_id>/', views.edit_volume_record, name='edit_volume_record'),
    path('trees/', views.trees_view, name='trees'),
    path('treecut-dash/', views.treecut_dash, name='treecut-dash'),
    path('developers/', views.developers, name='developers'),
    path('chainsaw-dash/', views.chainsaw_dash, name='chainsaw-dash'),
    path('get-last-chainsaw-number/', views.get_last_chainsaw_number, name='get_last_chainsaw_number'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # try:
    #     import debug_toolbar
    #     urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
    # except ImportError:
    #     pass
    