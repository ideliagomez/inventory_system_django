from django.urls import path
from . import views

urlpatterns = [
    #Demo
    path('demo-login/', views.login_demo, name='login_demo'),

    #Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Compras
    path('compras/', views.compra_list, name='compra_list'),
    path('compras/nueva/', views.compra_create, name='compra_create'), 
    path('compras/editar/<int:pk>/', views.compra_edit, name='compra_edit'),
    
    # Ventas
    path('ventas/', views.venta_list, name='venta_list'),
    path('ventas/nueva/', views.venta_create, name='venta_create'),
    path('ventas/editar/<int:pk>/', views.venta_edit, name='venta_edit'),
       
    # Inventario
    path('inventario/', views.inventario_list, name='inventario_list'),
    
    # Historial de precios
    path('historial-precios/', views.historial_precio_list, name='historial_precio_list'),

    # Catálogo principal
    path('catalogo/', views.catalogo_view, name='catalogo'),
    
    # URLs separadas pero todo en un template
    path('clientes/', views.clientes_view, name='clientes_view'),
    path('productos/', views.productos_view, name='productos_view'),
    path('proveedores/', views.proveedores_view, name='proveedores_view'),
   
    # Análisis de Ventas
    path('analisis-ventas/', views.analisis_ventas_list, name='analisis_ventas_list'),
    path('analisis-ventas/recalcular-todo/', views.analisis_ventas_recalcular_todo, name='analisis_ventas_recalcular_todo'),
]
    