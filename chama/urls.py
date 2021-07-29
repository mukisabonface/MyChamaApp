from django.urls import path, include, re_path
from . import views
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
    path('', views.homepage, name='home'),
    # path('daraja/stk-push', views.stk_push_callback, name='mpesa_stk_push_callback'),
    path('register/', views.signup, name='register'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('chama/create/', views.ChamaCreate.as_view(), name='create-chama'),
    path('chama/<uuid:pk>', views.ChamaDetailView.as_view(), name='chama_detail'),
    path('<uuid:pk>/addmember', views.ChamaAddMember, name='add-member'),
    path('<uuid:pk>/remove_member/<phone_number>', views.ChamaRemoveMember, name='remove-member'),
    path('mychamas/', views.CurrentUserChamas.as_view(), name="my-chamas"),
    path('<uuid:pk>/makepayment/', views.TransactionCreate.as_view(), name='pay'),
    # Loans
    path('requests/<uuid:pk>', views.ChamaLoanRequests.as_view(), name="chama-loans"),
    path('myloans/', views.CurrentUserLoans.as_view(), name="my-loans"),
    path('<uuid:pk>/loan/', views.RequestLoan.as_view(), name="request-loan"),
    path('approve/<int:pk>', views.approveLoan, name='approve-loan'),
    # Meetings
    path('<uuid:pk>/setmeeting/', views.SetMeeting.as_view(), name='set-meeting'),
    path('daraja/stk-push', views.stk_push_callback, name='mpesa_stk_push_callback'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
