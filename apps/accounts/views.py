from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .forms import UserRegistrationForm, UserLoginForm, ProfileEditForm, AccountDeleteForm
from .models import User


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=True)
            
            # Send Activation Email
            activation_url = request.build_absolute_uri(
                reverse('activate_account', kwargs={'token': str(user.verification_token)})
            )
            subject = "Activate Your CrowdFund Egypt Account"
            message = (
                f"Hello {user.get_full_name()},\n\n"
                f"Thank you for registering at CrowdFund Egypt!\n"
                f"Please click the link below within 24 hours to activate your account:\n\n"
                f"{activation_url}\n\n"
                f"If you did not register, please ignore this email."
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            messages.success(
                request,
                _("Registration successful! An activation link has been sent to your email. Please activate your account within 24 hours before logging in.")
            )
            return redirect('login')
        else:
            messages.error(request, _("Registration failed. Please correct the errors below."))
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def activate_account_view(request, token):
    try:
        user = User.objects.get(verification_token=token)
    except User.DoesNotExist:
        messages.error(request, _("Invalid activation link or account does not exist."))
        return redirect('login')

    if user.is_email_verified:
        messages.info(request, _("Your account is already activated. You can log in."))
        return redirect('login')

    if user.is_token_valid():
        user.is_email_verified = True
        user.is_active = True
        user.save(update_fields=['is_email_verified', 'is_active'])
        messages.success(request, _("Your account has been activated successfully! You can now log in."))
        return redirect('login')
    else:
        messages.error(request, _("The activation link has expired (24 hours window exceeded). Please contact support or register again."))
        return redirect('register')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.GET.get('next', 'home')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            # Verify if user exists first to check email verification state
            try:
                target_user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                target_user = None

            if target_user and not target_user.is_email_verified:
                messages.warning(
                    request,
                    _("Your email address is not verified yet. Please check your inbox for the 24-hour activation email.")
                )
                return render(request, 'accounts/login.html', {'form': form})

            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, _(f"Welcome back, {user.first_name}!"))
                return redirect(next_url)
            else:
                messages.error(request, _("Invalid email address or password."))
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, _("You have been logged out successfully."))
    return redirect('home')


@login_required
def profile_view(request):
    user = request.user
    user_projects = user.projects.all()
    user_donations = user.donations.select_related('project').all()
    delete_form = AccountDeleteForm()

    context = {
        'profile_user': user,
        'user_projects': user_projects,
        'user_donations': user_donations,
        'delete_form': delete_form,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit_view(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Your profile details have been updated successfully!"))
            return redirect('profile')
        else:
            messages.error(request, _("Please correct the errors in your profile form."))
    else:
        form = ProfileEditForm(instance=user)

    return render(request, 'accounts/profile_edit.html', {'form': form, 'user': user})


@login_required
def delete_account_view(request):
    if request.method == 'POST':
        form = AccountDeleteForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get('password')
            user = request.user
            if user.check_password(password):
                user.delete()
                messages.success(request, _("Your account has been deleted permanently."))
                return redirect('home')
            else:
                messages.error(request, _("Incorrect password. Account deletion cancelled."))
                return redirect('profile')
        else:
            messages.error(request, _("Invalid form submission for account deletion."))
            return redirect('profile')
    return redirect('profile')
