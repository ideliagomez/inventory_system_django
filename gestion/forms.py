from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
from django.utils import timezone

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo electrónico")
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {
            'username': 'Nombre de usuario',
            'password1': 'Contraseña',
            'password2': 'Confirmar contraseña',
        }

class CompraForm(forms.ModelForm):
    # Campos calculados
    costo_unitario = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={
        'class':'form-control', 'step':'0.01', 'readonly':'readonly'
    }))
    ganancia_unitaria = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={
        'class':'form-control', 'step':'0.01', 'readonly':'readonly'
    }))
    ganancia_total = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={
        'class':'form-control', 'step':'0.01', 'readonly':'readonly'
    }))

    class Meta:
        model = Compra
        fields = '__all__'
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'numero_factura': forms.TextInput(attrs={'class': 'form-control'}),
            'id_proveedor': forms.Select(attrs={'class': 'form-control'}),
            'id_producto': forms.Select(attrs={'class': 'form-control'}),
            'costo_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min':'1'}),
            'porcentaje_ganancia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'numero_factura': 'Número de Factura',
            'fecha': 'Fecha',
            'id_proveedor': 'Proveedor',
            'id_producto': 'Producto',
            'costo_total': 'Costo Total',
            'cantidad': 'Cantidad',
            'costo_unitario': 'Costo Unitario',
            'porcentaje_ganancia': 'Porcentaje de Ganancia (%)',
            'precio': 'Precio de Venta',
            'ganancia_unitaria': 'Ganancia Unitaria',
            'ganancia_total': 'Ganancia Total',
        }


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = '__all__'
        widgets = {
            'id_producto': forms.Select(attrs={'class': 'form-control'}),
            'id_cliente': forms.Select(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'id_producto': 'Producto',
            'id_cliente': 'Cliente',
            'precio': 'Precio',
            'cantidad': 'Cantidad',
        }

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = '__all__'
        widgets = {
            'empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'productos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class HistorialPrecioForm(forms.ModelForm):
    class Meta:
        model = HistorialPrecio
        fields = '__all__'
        widgets = {
            'id_producto': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'precio_sugerido': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'id_producto': 'Producto',
            'fecha': 'Fecha',
            'precio_sugerido': 'Precio Sugerido',
        }

#--------- Análisis de Ventas ------------
class AnalisisVentaFilterForm(forms.Form):
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha inicio'
    )
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha fin'
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por fecha...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer valores por defecto (últimos 30 días)
        hoy = timezone.now().date()
        mes_pasado = hoy - timezone.timedelta(days=30)
        
        if not self.initial.get('fecha_inicio'):
            self.initial['fecha_inicio'] = mes_pasado
        if not self.initial.get('fecha_fin'):
            self.initial['fecha_fin'] = hoy