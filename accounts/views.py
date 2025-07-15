from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.cache import cache

import requests
import time

from .models import PasswordVault, encrypt_password, decrypt_password

# ✅ Use Custom User Model
CustomUser = get_user_model()


# ---------- LOGIN ----------
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            if user.is_superuser or user.is_staff:
                return redirect('admin_dashboard')
            return redirect('user_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


# ---------- LOGOUT ----------
def logout_view(request):
    logout(request)
    return redirect('login')


# ---------- SIGNUP ----------
def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


# ---------- USER DASHBOARD ----------
@login_required
def user_dashboard(request):
    return render(request, 'accounts/user_dashboard.html')


# ---------- ADMIN DASHBOARD ----------
def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    inactive_users = total_users - active_users
    staff_users = CustomUser.objects.filter(is_staff=True).count()
    normal_users = total_users - staff_users

    users = CustomUser.objects.all()

    return render(request, 'accounts/admin_dashboard.html', {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'inactive_users': inactive_users,
        'normal_users': normal_users,
    })


# ---------- ADMIN ACTIONS ----------
@login_required
@user_passes_test(is_superuser)
def toggle_staff_status(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_staff = not user.is_staff
    user.save()

    # ✅ Refresh current session if you are updating yourself
    if request.user.id == user.id:
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)

    return redirect('admin_dashboard')


@login_required
@user_passes_test(is_superuser)
def toggle_superuser_status(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_superuser = not user.is_superuser
    user.save()

    # ✅ Refresh session for current user
    if request.user.id == user.id:
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)

    return redirect('admin_dashboard')




@login_required
@user_passes_test(is_superuser)
def toggle_active_status(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = not user.is_active
    user.save()
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_superuser)
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    return redirect('admin_dashboard')


# ---------- DATA LEAK SCANNER ----------
COOLDOWN_SECONDS = 10

@login_required
def data_leak_scanner(request):
    leak_result = None
    user_id = request.user.id
    cache_key = f"scanner_cooldown_{user_id}"

    if request.method == "POST":
        last_scan_time = cache.get(cache_key)
        current_time = time.time()

        if last_scan_time and current_time - last_scan_time < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (current_time - last_scan_time))
            messages.warning(request, f"⏳ Too many requests! Try again in {remaining} seconds.")
            return render(request, "accounts/data_leak_scanner.html", {"leak_result": leak_result})

        email = request.POST.get("email")
        api_url = f"https://leakcheck.io/api/public?check={email}"

        try:
            response = requests.get(api_url, headers={"User-Agent": "ChakraX"})
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("found"):
                    breaches = data.get("sources", [])
                    leak_result = {
                        "found": True,
                        "count": len(breaches),
                        "breaches": breaches
                    }
                else:
                    leak_result = {"found": False}

                cache.set(cache_key, current_time, timeout=COOLDOWN_SECONDS)
            else:
                messages.error(request, f"API Error: {response.status_code}")

        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, "accounts/data_leak_scanner.html", {"leak_result": leak_result})


# ---------- PASSWORD MANAGER ----------
@login_required
def password_manager(request):
    if request.method == "POST":
        site_name = request.POST.get("site_name")
        site_url = request.POST.get("site_url")
        username_or_email = request.POST.get("username_or_email")
        raw_password = request.POST.get("password")

        encrypted_pwd = encrypt_password(raw_password)

        PasswordVault.objects.create(
            user=request.user,
            site_name=site_name,
            site_url=site_url,
            username_or_email=username_or_email,
            encrypted_password=encrypted_pwd
        )
        messages.success(request, f"✅ Password for {site_name} saved securely!")
        return redirect("password_manager")

    saved_passwords = PasswordVault.objects.filter(user=request.user)
    for pwd in saved_passwords:
        pwd.decrypted_password = decrypt_password(pwd.encrypted_password)

    return render(request, "accounts/password_manager.html", {"passwords": saved_passwords})
