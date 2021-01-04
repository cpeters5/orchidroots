from django.urls import path, re_path

from . import views

app_name = 'donation'
urlpatterns = [
    path('donateapp/', views.DonateView.as_view(), name='donateapp'),
    path('donateapp/<int:donateamt>/', views.DonateView.as_view(), name='donateapp'),
    path('donate/', views.donate, name='donate'),
    path('donate/<int:donateamt>/', views.donate, name='donate'),
    path('donate/paypal-done/', views.PaypalTransactionDoneView.as_view(), name='paypal-done'),
    path('thank-you/<int:donateamt>/', views.ThankYouView.as_view(), name='thankyou'),
]
