from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Compras
    path('compras/', views.compra_list, name='compra_list'),
    path('compras/nueva/', views.compra_create, name='compra_create'),
    path('compras/editar/<int:pk>/', views.compra_edit, name='compra_edit'),
    path('compras/eliminar/<int:pk>/', views.compra_delete, name='compra_delete'),
    
    # Ventas
    path('ventas/', views.venta_list, name='venta_list'),
    path('ventas/nueva/', views.venta_create, name='venta_create'),
    path('ventas/editar/<int:pk>/', views.venta_edit, name='venta_edit'),
    path('ventas/eliminar/<int:pk>/', views.venta_delete, name='venta_delete'),
    
    # Catálogo
    path('catalogo/', views.catalogo_view, name='catalogo'),
    path('catalogo/cliente/nuevo/', views.cliente_create, name='cliente_create'),
    path('catalogo/producto/nuevo/', views.producto_create, name='producto_create'),
    path('catalogo/proveedor/nuevo/', views.proveedor_create, name='proveedor_create'),
    
    # Inventario
    path('inventario/', views.inventario_list, name='inventario_list'),
    
    # Historial de precios
    path('historial-precios/', views.historial_precio_list, name='historial_precio_list'),
    path('historial-precios/nuevo/', views.historial_precio_create, name='historial_precio_create'),
]