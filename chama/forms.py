from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Member, Chama, Transaction, ChamaMeetings, LoanRequests, Membership

from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

import re


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.widgets.TextInput(
        attrs={'placeholder': 'Firstname'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.widgets.TextInput(
        attrs={'placeholder': 'Lastname'}))
    email = forms.EmailField(max_length=254, widget=forms.widgets.EmailInput(
        attrs={'placeholder': 'e.g user@example.com'}))
    phone_number = forms.CharField(max_length=10, required=True, widget=forms.widgets.TextInput(
        attrs={'placeholder': 'e.g 0712345678', 'type': 'tel'}))

    class Meta:
        model = Member
        fields = ('username', 'first_name', 'last_name', 'email',
                  'phone_number', 'password1', 'password2')

    def clean_phone_number(self):

        data = self.cleaned_data['phone_number']

        if len(data) == 10:
            if data[0] in '0789' and all([i in '1234567890' for i in data]):
                pass
            else:
                raise ValidationError(_('Enter a correct Phone Number!'))
        else:
            raise ValidationError(
                _('Number is too short. Should be ten digits, including zero'))

        return data


class CreateChamaForm(ModelForm):

    class Meta:
        model = Chama
        fields = ('groupName', 'paybillNo',
                  'contribution_amnt', 'contribution_interval')
        labels = {'groupName': _('Group Name'),
                  'paybillNo': _('M-Pesa Paybill Number'),
                  'contribution_amnt': _('Contribution Amount'),
                  'contribution_interval': _('Contribution Interval')
                  }
        help_texts = {'groupName': _('e.g Mapato Investment Group'),
                      'paybillNo': _('e.g 568942'),
                      'contribution_amnt': _('Amount member should contribute at a time'),
                      }

    def clean_contribution_amnt(self):

        data = self.cleaned_data['contribution_amnt']

        if data < 0:
            raise ValidationError(_('Amount Less Than Zero!'))
        return data

    def clean_paybillNo(self):
        data = self.cleaned_data['paybillNo']

        if len(str(data)) >= 7:
            raise ValidationError(_('Enter correct Paybill Number!'))
        return data
    
    
class TransactionForm(ModelForm):
    class Meta:
        model = Transaction
        fields = ('amount', 'transaction_type')
        labels = {'amount': _('Enter Amount:'),
                  'transaction_type': _('Payment Type')
                  }

    def clean_amount(self):

        data = self.cleaned_data['amount']

        if data < 0:
            raise ValidationError(_('Amount Less Than Zero!'))
        return data


class AddMemberForm(forms.Form):
    phone = forms.CharField(max_length=30, required=True, widget=forms.widgets.TextInput(
        attrs={'placeholder': 'Enter Phone Number'}))

    def clean_phone(self):

        data = self.cleaned_data['phone']

        if len(data) == 10:
            if data[0] in '0789' and all([i in '1234567890' for i in data]):
                pass
            else:
                raise ValidationError(_('Enter a correct Phone Number!'))
        else:
            raise ValidationError(
                _('Number is too short. Should be ten digits, including zero'))

        return data


class SetMeetingForm(ModelForm):
    class Meta:
        model = ChamaMeetings
        fields = ('meeting_date', 'location')
        labels = {'meeting_date': _('Enter Date:'),
                  'location': _('Where will the meeting take place?')
                  }
        help_texts = {'meeting_date': _('Format: YYYY-MM-DD'),
                      'location': _('e.g Blue Springs Hotel, Thika')
                      }
        # widgets = {
        #     'meeting': forms.SplitDateTimeField(),
        # }


class RequestLoan(ModelForm):
    class Meta:
        model = LoanRequests
        fields = ('amount',)
        labels = {'amount': _('Amount'),
                  }
