from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model

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
    staff_users = CustomUser.objects.filter(is_staff=True).count()

    users = CustomUser.objects.all()
    return render(request, 'accounts/admin_dashboard.html', {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
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
