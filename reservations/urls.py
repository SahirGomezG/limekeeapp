from django.urls import path
from .views import ReservationListView, ReservationDetailView, ReservationUpdateView, UserReservationListView, Progress, Calendar
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    path('', ReservationListView.as_view(), name='reservation-home'),
    path('user/<str:username>', UserReservationListView.as_view(), name='user-reservations'),
    path('<slug:pk>', ReservationDetailView.as_view(), name='reservation-detail'),
    #path('<slug:pk>/payment', HomePageView.as_view(), name='home-payment-'),
    path('processed/<slug:pk>/', views.charge, name='charge-reservation'),
    path('reservations_metrics/', views.metrics, name='reservations-metrics'),
    path('reservations_progress/', Progress.as_view(), name='reservations-progress'),
    path('reservations_summary/', views.summary, name='reservations-summary'),
    path('reservations_global/', views.global_list, name='reservations-global-list'),
    path('reservation_create_form/', views.reservation_create_form, name='reservation1'),
    path('reservations_calendar/', Calendar.as_view(), name='reservations-calendar'),

]
