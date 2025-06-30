from django.urls import path,include
from . import views
app_name = 'store'
urlpatterns = [
    path('',views.product_list, name='product_list'),
    path('product/<int:id>/', views.product_details, name='product_details'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add-to-cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('signup/', views.signup_view, name='signup'),
    path('login',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('orders/', views.order_history, name='order_history'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.checkout_success, name='checkout_success'),
    path('cancel/', views.checkout_cancel, name='checkout_cancel'),
]