from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Transaction, Category, Account, Budget

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError('Passwords do not match')
        return cleaned

class TransactionForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    class Meta:
        model = Transaction
        fields = ['account','category','type','amount','date','note']

class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if self.user:
            qs = Category.objects.filter(
                user=self.user,
                name=cleaned.get('name'),
                type=cleaned.get('type')
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if cleaned.get('name') and cleaned.get('type') and qs.exists():
                raise forms.ValidationError('Category with this name and type already exists.')
        return cleaned

    class Meta:
        model = Category
        fields = ['name','type']

class AccountForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if self.user:
            qs = Account.objects.filter(user=self.user, name=cleaned.get('name'))
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if cleaned.get('name') and qs.exists():
                raise forms.ValidationError('Account with this name already exists.')
        return cleaned

    class Meta:
        model = Account
        fields = ['name','balance']  # balance = opening balance

class TransferForm(forms.Form):
    from_account = forms.ModelChoiceField(queryset=Account.objects.none())
    to_account   = forms.ModelChoiceField(queryset=Account.objects.none())
    amount       = forms.DecimalField(min_value=0.01, max_digits=12, decimal_places=2)
    date         = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    note         = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        qs = Account.objects.filter(user=user).order_by('name')
        self.fields['from_account'].queryset = qs
        self.fields['to_account'].queryset = qs

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('from_account') == cleaned.get('to_account'):
            raise forms.ValidationError('From and To accounts must be different.')
        return cleaned

class BudgetForm(forms.ModelForm):
    month = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    class Meta:
        model = Budget
        fields = ['category','month','amount']