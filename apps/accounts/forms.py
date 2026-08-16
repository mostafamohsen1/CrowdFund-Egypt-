from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .validators import validate_egyptian_phone

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-control'}),
        help_text=_("At least 8 characters long.")
    )
    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'e.g. Ahmed', 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'e.g. Hassan', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'ahmed@example.com', 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '01012345678 or +201123456789', 'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("An account with this email address already exists."))
        return email.lower()

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', _("Passwords do not match."))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = True  # Can log in only after email activation check in view
        user.is_email_verified = False
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    email = forms.EmailField(
        label=_("Email Address"),
        widget=forms.EmailInput(attrs={'placeholder': 'you@example.com', 'class': 'form-control'})
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-control'})
    )


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'profile_picture', 'birthdate', 'facebook_profile', 'country']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'birthdate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'facebook_profile': forms.URLInput(attrs={'placeholder': 'https://facebook.com/yourprofile', 'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AccountDeleteForm(forms.Form):
    password = forms.CharField(
        label=_("Confirm your password to delete your account"),
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your current password',
            'class': 'form-control'
        }),
        help_text=_("This action is permanent and cannot be undone.")
    )
