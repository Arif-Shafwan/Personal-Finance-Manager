from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),

    # Transactions
    path('transactions/', views.transaction_list, name='transactions'),
    path('transactions/new/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.transaction_update, name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),

    # Categories
    path('categories/', views.category_list, name='categories'),
    path('categories/new/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Accounts
    path('accounts/', views.account_list, name='accounts'),
    path('accounts/new/', views.account_create, name='account_create'),
    path('accounts/<int:pk>/edit/', views.account_update, name='account_update'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),
    path('accounts/transfer/', views.account_transfer, name='account_transfer'),

    # Budgets
    path('budgets/', views.budget_list, name='budgets'),
    path('budgets/new/', views.budget_create, name='budget_create'),
    path('budgets/<int:pk>/edit/', views.budget_update, name='budget_update'),
    path('budgets/<int:pk>/delete/', views.budget_delete, name='budget_delete'),
]