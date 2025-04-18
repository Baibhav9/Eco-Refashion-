from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []
    
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            # Ensure the user is logged in
            if not request.user.is_authenticated:
                return redirect('login')  # or your login URL name
            
            # Check if the user role is allowed
            if request.user.role in allowed_roles:
                return func(request, *args, **kwargs)
            
            # Optionally, redirect to an unauthorized page or raise an error
            raise PermissionDenied("You are not authorized to view this page.")
        return wrapper
    return decorator
