from django.contrib import admin
from .models import *

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id_cliente', 'nombre', 'apellido', 'fecha_creacion')
    search_fields = ('nombre', 'apellido')
    list_filter = ('fecha_creacion',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id_producto', 'nombre', 'marca', 'fecha_creacion')
    search_fields = ('nombre', 'marca')

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('id_proveedor', 'empresa', 'telefono', 'fecha_creacion')
    search_fields = ('empresa', 'telefono', 'productos')

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id_compra', 'numero_factura', 'fecha', 'id_proveedor', 'id_producto', 'costo_total', 'cantidad')
    list_filter = ('fecha', 'id_proveedor')
    search_fields = ('numero_factura',)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id_venta', 'id_producto', 'id_cliente', 'precio', 'cantidad', 'fecha_creacion')
    list_filter = ('fecha_creacion', 'id_cliente')
    date_hierarchy = 'fecha_creacion'

@admin.register(HistorialPrecio)
class HistorialPrecioAdmin(admin.ModelAdmin):
    list_display = ('id_precio', 'id_producto', 'fecha', 'precio_sugerido')
    list_filter = ('fecha',)
    date_hierarchy = 'fecha'