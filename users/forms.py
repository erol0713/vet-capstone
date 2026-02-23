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
    last_name = forms.CharField(max_length=50, required=False, label='Last Name (Surname)')
    middle_name = forms.CharField(max_length=50, required=False, label='Middle Name')
    first_name = forms.CharField(max_length=50, required=False, label='First Name')

    class Meta:
        model = UserProfile
        fields = ('full_name', 'gender', 'address', 'age', 'birthday', 'profile_photo')
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
        }

    @staticmethod
    def _split_full_name(full_name: str):
        value = (full_name or '').strip()
        if not value:
            return '', '', ''
        if ',' in value:
            chunks = [chunk.strip() for chunk in value.split(',')]
            if len(chunks) >= 3:
                # Legacy format support: "Last, Middle, First"
                return chunks[0], chunks[1], ' '.join(chunks[2:])
            if len(chunks) == 2:
                return chunks[0], '', chunks[1]
            return '', '', chunks[0]

        parts = value.split()
        if len(parts) == 1:
            return '', '', parts[0]
        if len(parts) == 2:
            # New format: "First Last"
            return parts[1], '', parts[0]
        # New format: "First Middle Last"
        return parts[-1], ' '.join(parts[1:-1]), parts[0]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            last_name, middle_name, first_name = self._split_full_name(
                getattr(self.instance, 'full_name', '')
            )
            self.fields['last_name'].initial = last_name
            self.fields['middle_name'].initial = middle_name
            self.fields['first_name'].initial = first_name

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')
        self.fields['age'].widget.attrs.setdefault('readonly', 'readonly')
        self.fields['profile_photo'].widget.attrs.setdefault('accept', 'image/*')

    def clean(self):
        cleaned = super().clean()
        last_name = (cleaned.get('last_name') or '').strip()
        middle_name = (cleaned.get('middle_name') or '').strip()
        first_name = (cleaned.get('first_name') or '').strip()

        if any([last_name, middle_name, first_name]):
            cleaned['full_name'] = ' '.join(
                part for part in [first_name, middle_name, last_name] if part
            )
        else:
            fallback_full_name = (cleaned.get('full_name') or '').strip()
            if not fallback_full_name and self.instance and self.instance.pk:
                fallback_full_name = (self.instance.full_name or '').strip()
            cleaned['full_name'] = fallback_full_name

        birthday = cleaned.get('birthday')
        if birthday:
            today = timezone.now().date()
            age = today.year - birthday.year - (
                (today.month, today.day) < (birthday.month, birthday.day)
            )
            cleaned['age'] = max(age, 0)
        return cleaned
