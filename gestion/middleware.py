# tu_app/middleware.py
from django.http import HttpResponseForbidden

class DemoRestrictionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated and request.user.username == 'demo':
            
            # Bloquear métodos de modificación
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                
                allowed_urls = [
                    '/logout/',
                    '/demo-login/',
                ]
                
                if request.path not in allowed_urls:
                    return HttpResponseForbidden(
                        "Modo demostración - Solo lectura\n"
                        "El usuario demo no puede crear, editar o eliminar datos."
                    )
        
        return self.get_response(request)