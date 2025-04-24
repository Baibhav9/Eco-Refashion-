from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView, CreateView

from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm


class RegisterView(CreateView):
    template_name = "accounts/register.html"
    model = get_user_model()
    form_class = CustomUserCreationForm

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
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:login")
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
            return self.render_to_response(self.get_context_data(form=form))


class LoginView(TemplateView):
    template_name = 'accounts/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = AuthenticationForm()
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

        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('main:index')
        else:
            form = AuthenticationForm()
        context.update({
            'form': form
        })
        return self.render_to_response(context)


class LogoutView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/logout.html"

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect('main:index')
