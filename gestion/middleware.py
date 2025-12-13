# tu_app/middleware.py
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages

class DemoRestrictionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar si es usuario demo
        if request.user.is_authenticated and request.user.username == 'demo':
            
            # ========== BLOQUEAR ACCIONES ==========
        
            action = request.GET.get('action', '')
            if action in ['create', 'edit', 'delete']:
                messages.error(request, self.get_action_message(action))
                return redirect(self.get_redirect_url(request))
            
            if request.method == 'POST':
                
                if request.path not in ['/logout/', '/demo-login/']:
                    messages.error(request, self.get_post_message())
                    return redirect(self.get_redirect_url(request))
            
            
            blocked_paths = [
                '/compras/nueva/',
                '/compras/editar/',
                '/ventas/nueva/',
                '/ventas/editar/',
            ]
            
            for path in blocked_paths:
                if request.path.startswith(path):
                    messages.warning(request, "Modo demostración - Acceso restringido")
                    return redirect('dashboard')
        
        response = self.get_response(request)
        return response
    
    def get_action_message(self, action):
        """Mensaje según la acción intentada"""
        messages_dict = {
            'create': 'No puedes crear nuevos registros en modo demostración.',
            'edit': 'No puedes editar registros en modo demostración.',
            'delete': 'No puedes eliminar registros en modo demostración.',
        }
        return f" {messages_dict.get(action, 'Acción no permitida')}"
    
    def get_post_message(self):
        """Mensaje para formularios POST"""
        return (
            "Formulario bloqueado - Modo demostración\n"
            "Para usar todas las funcionalidades, registra tu propia cuenta."
        )
    
    def get_redirect_url(self, request):
        """Determina a dónde redirigir"""
        # Intentar redirigir a la página anterior
        referer = request.META.get('HTTP_REFERER')
        if referer and referer.startswith(request.build_absolute_uri('/')[:-1]):
            return referer
        # Si no, al dashboard
        return 'dashboard'