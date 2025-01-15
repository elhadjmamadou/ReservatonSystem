from django.urls import path
from app import views
from django.contrib.auth import views as auth_views
from .views import ResourceListView, ReservationCreateView, ReservationUpdateView, ReservationDeleteView



urlpatterns = [
    path('', views.home, name='home'),
    path('register', views.register, name='register'),
    path('login', views.logIn, name='login'),
    path('logout', views.logOut, name='logout'),
    path('activate/<uidb64>/<token>',views.activate, name='activate'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('profile/', views.profile, name='profile'),
    path('manage-reservations/', views.manage_reservations, name='manage_reservations'),  # Route pour la gestion des réservations par l'admin
    path('reservations/json/', views.ReservationListView.as_view(), name='reservation_json'),
    path('resources/', ResourceListView.as_view(), name='resource_list'),
    path('reservations/create/', ReservationCreateView.as_view(), name='reservation_create'),
    path('reservations/<int:pk>/update/', ReservationUpdateView.as_view(), name='reservation_update'),
    path('reservations/<int:pk>/delete/', ReservationDeleteView.as_view(), name='reservation_delete'),
]
