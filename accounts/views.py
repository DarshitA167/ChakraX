from urllib import response
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
import requests
from django.contrib import messages

# ✅ Use Custom User Model
CustomUser = get_user_model()


# ---------- LOGIN VIEW ----------
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # ✅ Handle next URL (for @login_required redirects)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            # ✅ Role-based redirection
            if user.is_superuser or user.is_staff:
                return redirect('admin_dashboard')
            return redirect('user_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


# ---------- LOGOUT VIEW ----------
def logout_view(request):
    logout(request)
    return redirect('login')


# ---------- SIGNUP VIEW ----------
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


# ---------- ADMIN DASHBOARD HELPERS ----------
def is_superuser(user):
    return user.is_superuser


# ---------- ADMIN DASHBOARD ----------
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
    return redirect('admin_dashboard')


@login_required
@user_passes_test(is_superuser)
def toggle_superuser_status(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_superuser = not user.is_superuser
    user.save()
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



import time
from django.core.cache import cache
import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

COOLDOWN_SECONDS = 10  # 🔥 Adjust as you like

@login_required
def data_leak_scanner(request):
    leak_result = None
    user_id = request.user.id  # unique per user
    cache_key = f"scanner_cooldown_{user_id}"

    if request.method == "POST":
        # ✅ Check cooldown
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
            print("STATUS CODE:", response.status_code)
            print("RAW TEXT:", response.text[:500])

            if response.status_code == 200:
                data = response.json()
                print("API RESPONSE (JSON):", data)

                if data.get("success") and data.get("found"):
                    breaches = data.get("sources", [])
                    leak_result = {
                        "found": True,
                        "count": len(breaches),
                        "breaches": breaches
                    }
                else:
                    leak_result = {"found": False}
                
                # ✅ Save new scan time
                cache.set(cache_key, current_time, timeout=COOLDOWN_SECONDS)
            else:
                messages.error(request, f"API Error: {response.status_code}")

        except Exception as e:
            messages.error(request, f"Error: {e}")
            print("ERROR OCCURRED:", e)

    return render(request, "accounts/data_leak_scanner.html", {"leak_result": leak_result})
