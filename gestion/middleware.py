# middleware.py 
class DemoRestrictionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        user_demo = os.environ.get('USER_DEMO', 'demo')
        
        if (request.user.is_authenticated and 
            request.user.username == user_demo and
            request.method in ['POST', 'PUT', 'DELETE', 'PATCH']):
            
            allowed_for_modification = [
                '/demo-login/',
                '/logout/',
            ]
            
            if request.path not in allowed_for_modification:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(
                    "⚠️ Modo demostración - Solo lectura. "
                    "Contacta al administrador para editar datos."
                )
        
        return self.get_response(request)