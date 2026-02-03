from django import forms
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm

from .models import CustomUser, UserProfile


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    legal_consent = forms.BooleanField(required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['legal_consent'].widget.attrs.update({'class': 'form-check-input'})

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered.')
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            self.add_error('password2', 'Passwords do not match.')
        return cleaned


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned = super().clean()
        identifier = cleaned.get('username')
        password = cleaned.get('password')
        if identifier and password:
            user = authenticate(self.request, username=identifier, password=password)
            if user is None and '@' in identifier:
                matched = CustomUser.objects.filter(email=identifier).first()
                if matched:
                    user = authenticate(self.request, username=matched.username, password=password)
            if user is None:
                raise forms.ValidationError('Invalid username/email or password.')
        return cleaned


class OTPVerifyForm(forms.Form):
    code = forms.CharField(max_length=6)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].widget.attrs.update({'class': 'form-control', 'maxlength': 6})


class FaceVerificationSubmitForm(forms.Form):
    confirm = forms.BooleanField(
        required=True, label='I agree to submit my face verification for review.'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['confirm'].widget.attrs.update({'class': 'form-check-input'})


class ProfileInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('full_name', 'address', 'age', 'birthday')
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['age'].widget.attrs.setdefault('readonly', 'readonly')

    def clean(self):
        cleaned = super().clean()
        birthday = cleaned.get('birthday')
        if birthday:
            today = timezone.now().date()
            age = today.year - birthday.year - (
                (today.month, today.day) < (birthday.month, birthday.day)
            )
            cleaned['age'] = max(age, 0)
        return cleaned
