from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from .models import Member, Chama, Transaction, LoanRequests, ChamaMeetings, Membership
from .forms import RegisterForm, CreateChamaForm, TransactionForm, AddMemberForm, SetMeetingForm, RequestLoan
from django.conf import settings
from django.contrib.auth.decorators import login_required

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django_daraja.mpesa.core import MpesaClient
from django.contrib import messages


@login_required
def homepage(request):
    return render(request, 'chama/home_view.html')


def signup(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=email, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'chama/register.html', {'form': form})

# Create,update and list chamas, you can also access chama details


class ChamaCreate(CreateView):
    model = Chama
    form_class = CreateChamaForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        chama = form.save()
        m1 = Membership.objects.create(
            member=self.request.user, chama=chama, date_joined=timezone.now())
        return super().form_valid(form)


class ChamaUpdate(UpdateView):
    model = Chama
    fields = ['groupName', 'paybillNo',
              'contribution_amnt', 'contribution_interval']


class CurrentUserChamas(ListView):
    model = Chama
    template_name = 'chama/chama_list_current_user.html'
    paginate_by = 10

    def get_queryset(self):
        return Chama.objects.filter(created_by=self.request.user) | Chama.objects.filter(
            members__phone_number=self.request.user.phone_number)


class ChamaListView(ListView):
    model = Chama


class ChamaDetailView(DetailView):
    model = Chama

    def get_context_data(self, **kwargs):
        chama = get_object_or_404(Chama, pk=self.kwargs['pk'])
        context = super(ChamaDetailView, self).get_context_data(**kwargs)
        context['arrears'] = chama.get_member_arrears
        context['deposits'] = chama.get_member_deposits

        return context


@login_required
def ChamaAddMember(request, pk):
    """Add member to a chama"""

    chama = get_object_or_404(Chama, chama_id=pk)
    if request.method == 'POST':
        form = AddMemberForm(request.POST)
        if form.is_valid():
            phonenumber = form.cleaned_data['phone']
            member = Member.objects.get(phone_number=phonenumber)
            date_joined = timezone.now()
            if member in chama.members.all():
                messages.error(
                    request, 'Oops, user is already a member of this group')
            else:
                m1 = Membership(member=member, chama=chama,
                                date_joined=date_joined)
                m1.save()
                url = chama.get_absolute_url()
                return redirect(url)

    else:
        form = AddMemberForm()
    return render(request, 'chama/add_member.html', {'form': form, 'key': pk})


def ChamaRemoveMember(request, pk, phone_number):
    chama = get_object_or_404(Chama, chama_id=pk)
    member = Member.objects.get(phone_number=phone_number)
    # Now remove the member
    m1 = Membership.objects.filter(chama=chama).filter(member=member)
    m1.delete()
    chama.save()
    return redirect('chama_detail', pk)

# End chama models


class TransactionCreate(CreateView):
    model = Transaction
    form_class = TransactionForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        """Add other fields required before saving the transaction"""
        cl = MpesaClient()
        chama = get_object_or_404(Chama, pk=self.kwargs['pk'])
        phone = self.request.user.phone_number
        amount = form.cleaned_data['amount']
        description = form.cleaned_data['transaction_type']
        form.instance.chama = chama
        form.instance.transaction_time = timezone.now()
        form.instance.phone_number = phone
        form.instance.member = self.request.user
        # callback_url = self.request.build_absolute_uri(reverse('mpesa_stk_push_callback'))
        # response = cl.stk_push(phone, int(amount), chama.groupName, description, callback_url)
        # return HttpResponse(response.text)

        return super().form_valid(form)


def stk_push_callback(request):
    # Notification received from MPESA here.
    pass


class TransactionDetailView(DetailView):
    pass


class TransactionListView(ListView):
    pass

# End transactions view


class SetMeeting(CreateView):
    """View for setting a meeting"""
    model = ChamaMeetings
    form_class = SetMeetingForm
    template_name = "chama/set_meeting.html"
    success_url = reverse_lazy('home')
    paginate_by = 7

    def form_valid(self, form):
        """Add other fields required before saving the meeting"""
        chama = get_object_or_404(Chama, pk=self.kwargs['pk'])
        form.instance.chama = chama
        return super().form_valid(form)


class RequestLoan(CreateView):
    model = LoanRequests
    form_class = RequestLoan
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        """Add other fields"""
        chama = get_object_or_404(Chama, pk=self.kwargs['pk'])
        form.instance.user = self.request.user
        form.instance.chama = chama
        return super().form_valid(form)


class CurrentUserLoans(ListView):
    model = LoanRequests
    template_name = 'chama/loans_list_current_user.html'
    paginate_by = 10

    def get_queryset(self):
        return LoanRequests.objects.filter(user=self.request.user).filter(is_approved=True).exclude(is_paid=True)


class ChamaLoanRequests(ListView):
    model = LoanRequests
    template_name = 'chama/chama_requests.html'
    paginate_by = 5

    def get_queryset(self):
        chama = get_object_or_404(Chama, pk=self.kwargs['pk'])
        return LoanRequests.objects.filter(chama=chama).filter(is_approved=False)


def approveLoan(request, pk):
    """Admin approve loan"""
    loan = LoanRequests.objects.get(pk=pk)
    chama = loan.chama.pk
    loan.is_approved = True
    loan.save()
    return redirect('chama_detail', chama)
