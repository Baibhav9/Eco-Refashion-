from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView

from .forms import CustomUserCreationForm, LoginForm, CustomUserChangeForm
from ..main.constants import Roles


class RegisterView(CreateView):
    template_name = "accounts/register.html"
    form_class = CustomUserCreationForm
    object = get_user_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = CustomUserCreationForm()
        context.update({
            'form': form,
        })
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("main:index")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        post_data = request.POST.copy()

        if 'role' not in post_data:
            post_data['role'] = Roles.USER

        form = CustomUserCreationForm(post_data, request.FILES)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:login")

        context.update({
            'form': form
        })
        messages.error(request, "Registration failed. Please correct the errors below.")
        return self.render_to_response(self.get_context_data(form=form))


class LoginView(TemplateView):
    template_name = 'accounts/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = LoginForm()
        context.update({
            'form': form
        })
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("main:index")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('main:index')

        context.update({
            'form': form
        })
        return self.render_to_response(context)


class LogoutView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/logout.html"

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect('main:index')

class UserProfileView(LoginRequiredMixin, UpdateView):
    object = get_user_model()
    template_name = "accounts/profile.html"
    queryset = object.objects.all()
    fields = ['first_name', 'last_name', 'email', 'username', 'profile_image']

    def get_object(self, queryset = None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy("accounts:profile")

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_url = '/accounts/profile/'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


class UserProfileUpdate(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = CustomUserChangeForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user


