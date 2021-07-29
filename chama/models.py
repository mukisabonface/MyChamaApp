from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from djmoney.models.fields import MoneyField
import uuid
from django.core.exceptions import ObjectDoesNotExist
from datetime import timedelta, date
from django.utils import timezone
import datetime
import math


class Member(AbstractUser):
    phone_number = models.CharField(
        unique=True, max_length=10)
    email = models.EmailField(max_length=254, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']

    def __str__(self):
        return self.email

    def get_chamas(self):
        """Get all the chamas where the user is either an admin or a member"""
        ismember = self.membership_set.all().count()
        return ismember

    def get_my_savings(self):
        """Get all the user's savings"""
        transactions = self.transactions.all()
        savings = 0
        for transaction in transactions:
            if transaction.transaction_type == 'd':
                i = transaction.amount
                savings += i

        return savings

    def get_my_loans(self):
        loans = self.my_loan_requests.filter(
            is_approved=True).filter(is_paid=False)
        total = 0
        for loan in loans:
            i = loan.amount
            total += i
        return total

    def my_chama_shares(self):
        pass


class Chama(models.Model):
    """Model representing a chama
    """
    chama_id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                help_text='Unique ID for this particular chama across whole app')
    groupName = models.CharField(max_length=255, unique=True)
    paybillNo = models.PositiveIntegerField(unique=True)
    contribution_amnt = models.DecimalField(
        max_digits=10, decimal_places=2)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='chama', through='Membership', blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin')
    PAYMENT_TYPE = (
        ('d', 'Daily'),
        ('w', 'Weekly'),
        ('m', 'Monthly'),
        ('q', 'Quartely')
    )
    contribution_interval = models.CharField(max_length=1, choices=PAYMENT_TYPE,
                                             blank=True, default='d', help_text='Contribution Intervals')

    class Meta:
        ordering = ['groupName']

    def __str__(self):
        return self.groupName

    def get_absolute_url(self):
        return reverse("chama_detail", kwargs={"pk": self.pk})

    def get_members(self):
        """Get number of members"""
        members = self.members.all().count()
        return members

    def get_admin(self):
        """Get admin"""
        return self.created_by

    def get_total_balance(self):
        """Get account balance"""
        loans = self.loan_requests.filter(is_approved=True)
        total_loans = 0
        for loan in loans:
            amount = loan.amount
            total_loans += amount

        # Get total income
        payments = self.transactions.all()
        total_income = 0
        for payment in payments:
            amount = payment.amount
            total_income += amount

        balance = total_income - total_loans
        return balance

    def get_next_meeting(self):
        """Get meeting coming up in four weeks days."""
        months_time = datetime.date.today() + datetime.timedelta(weeks=4)
        meeting = self.meetings.get(meeting_date__lt=months_time)
        return meeting

    def total_approved_loans(self):
        """get all loans that have been approved in this chama"""
        loans = self.loan_requests.filter(is_approved=True)
        total_loans = 0
        for i in loans:
            amount = i.amount
            total_loans += amount
        return total_loans

    def get_member_deposits(self):
        """deposits of an individual member to this chama"""
        deposits = {}
        for member in self. members.all():
            transactions = member.transactions.filter(
                chama=self).filter(transaction_type='d')
            savings = 0
            for transaction in transactions:
                i = transaction.amount
                savings += i
            deposits[member] = savings
        return deposits

    def get_member_arrears(self):
        """Arrears of an individual member to this chama"""
        # get the member
        records = {}
        for member in self.members.all():
            # get the day member joined the group
            date_joined = member.date_joined
            today = datetime.datetime.now(timezone.utc)
            delta = today - date_joined

            # get the number of days, weeks or months that have passed since then
            days_passed = delta.days
            weeks_passed = days_passed // 7
            months_passed = days_passed // 30

            # if monthly
            if self.contribution_interval == 'm' and months_passed > 0:
                # get the amount he should have contributed by now
                deposits_by_now = self.contribution_amnt * months_passed
                # get amount he has contributed so far
                transactions = member.transactions.filter(
                    chama=self).filter(transaction_type='d')
                savings = 0
                for transaction in transactions:
                    i = transaction.amount
                    savings += i

                arrears = deposits_by_now - savings
                records[member] = arrears

            # if weekly
            elif self.contribution_interval == 'w' and weeks_passed > 0:
                # get the amount he should have contributed by now
                deposits_by_now = self.contribution_amnt * weeks_passed
                # get amount he has contributed so far
                transactions = member.transactions.filter(
                    chama=self).filter(transaction_type='d')
                savings = 0
                for transaction in transactions:
                    i = transaction.amount
                    savings += i

                arrears = deposits_by_now - savings
                records[member] = arrears

            # if daily
            elif self.contribution_interval == 'd' and days_passed > 0:

                # get amount he has contributed so far
                transactions = member.transactions.filter(
                    chama=self).filter(transaction_type='d')
                savings = 0
                # get the amount he should have contributed by now
                deposits_by_now = (self.contribution_amnt) * days_passed
                for transaction in transactions:
                    i = transaction.amount
                    savings += i

                arrears = deposits_by_now - savings
                records[member] = arrears
            else:
                pass
        return records


class Membership(models.Model):
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, on_delete=models.CASCADE)
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=False)

    # def get_my_chamasavings(self):
    #     """Get all the user's savings in a chama"""
    #     chama = self.chama
    #     transactions = self.member.transactions.filter(chama=chama)
    #     savings = 0
    #     for transaction in transactions:
    #         if transaction.transaction_type == 'd':
    #             i = transaction.amount
    #             savings += i

    #     return savings

    def get_my_chamaloans(self):
        """Loans owed to a particular chama"""
        loans = self.member.my_loan_requests.filter(
            is_approved=True).filter(is_paid=False).filter(chama=self.chama)
        total = 0
        for loan in loans:
            i = loan.amount
            total += i
        return total


class Transaction(models.Model):
    """This model defines all the transactions that take place, e.g fines or deposits
    Also includes the user who carried out the transaction and the code.
    """
    chama = models.ForeignKey(
        Chama, on_delete=models.DO_NOTHING, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_time = models.DateTimeField(auto_now_add=False)

    phone_number = models.CharField(blank=True, max_length=10)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, on_delete=models.DO_NOTHING, related_name='transactions')
    PAYMENT_TYPE = (
        ('f', 'Fine'),
        ('d', 'Deposit'),
        ('l', 'Loan')
    )
    transaction_type = models.CharField(max_length=1, choices=PAYMENT_TYPE,
                                        blank=True, default='d', help_text='I am paying for? Deposit,Fine or Loan')

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.phone_number

    def save(self, *args, **kwargs):
        """Deduct paid loan"""
        if self.transaction_type == 'l':
            loans = LoanRequests.objects.filter(chama=self.chama).filter(
                user=self.member).filter(is_approved=True)

            for i in loans:
                if i.amount > 0:
                    amount = i.amount - self.amount
                    i.amount = amount
                    i.save()
                else:
                    i.is_paid = True
                    i.save()
        super().save(*args, **kwargs)


class LoanRequests(models.Model):
    """This model stores all the user requests for a loan in a particular chama"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='my_loan_requests')
    is_approved = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    chama = models.ForeignKey(
        Chama, on_delete=models.DO_NOTHING, related_name='loan_requests')
    is_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f'{self.chama} {self.amount} {self.user.phone_number}'

    def get_absolute_url(self):
        return reverse("request-loan", kwargs={"pk": self.chama.pk})


class ChamaMeetings(models.Model):
    """Meetings with venues"""
    chama = models.ForeignKey(
        Chama, on_delete=models.DO_NOTHING, related_name='meetings')
    meeting_date = models.DateTimeField(blank=False, auto_now_add=False)
    location = models.TextField(blank=True, max_length=300)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f'On {self.meeting_date}, at {self.location}'

    def get_date(self):
        return 'foo'

    def get_absolute_url(self):
        return reverse("chama-detail", kwargs={"pk": self.chama.pk})
