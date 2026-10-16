from django.urls import path
from . import views

urlpatterns = [
    # Public & Landing
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('security-disclaimer/', views.security_disclaimer_view, name='security_disclaimer'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/password/', views.password_change_view, name='password_change'),
    path('demo-login/<str:username>/', views.quick_demo_login_view, name='quick_demo_login'),

    # Voter Experience
    path('dashboard/', views.voter_dashboard_view, name='voter_dashboard'),
    path('election/<slug:slug>/', views.election_detail_view, name='election_detail'),
    path('election/<slug:slug>/compare/', views.candidate_compare_view, name='candidate_compare'),
    
    # Voting Flow
    path('election/<slug:slug>/vote/', views.vote_select_view, name='vote_select'),
    path('election/<slug:slug>/confirm/', views.vote_confirm_view, name='vote_confirm'),
    path('election/<slug:slug>/submit/', views.vote_submit_view, name='vote_submit'),
    path('election/<slug:slug>/receipt/<str:receipt>/', views.vote_receipt_view, name='vote_receipt'),

    # Results
    path('election/<slug:slug>/results/', views.results_view, name='results'),

    # Administrator Management Portal
    path('admin-portal/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-portal/elections/new/', views.admin_election_create_view, name='admin_election_create'),
    path('admin-portal/elections/<slug:slug>/edit/', views.admin_election_edit_view, name='admin_election_edit'),
    path('admin-portal/elections/<slug:slug>/status/', views.admin_status_change_view, name='admin_status_change'),
    path('admin-portal/elections/<slug:slug>/publish/', views.admin_publish_results_view, name='admin_publish_results'),
    path('admin-portal/elections/<slug:slug>/candidates/new/', views.admin_candidate_create_view, name='admin_candidate_create'),
    path('admin-portal/candidates/<int:candidate_id>/edit/', views.admin_candidate_edit_view, name='admin_candidate_edit'),
    path('admin-portal/candidates/<int:candidate_id>/delete/', views.admin_candidate_delete_view, name='admin_candidate_delete'),
    path('admin-portal/audit-logs/', views.admin_audit_logs_view, name='admin_audit_logs'),
]
