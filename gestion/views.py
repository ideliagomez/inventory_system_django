from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q
from django.db import connection
from .models import *
from .forms import *
from django.utils import timezone
from .utils import get_inventario_data, get_inventario_producto, get_estadisticas_inventario


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Registro exitoso!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    # Estadísticas para el dashboard
    total_productos = Producto.objects.count()
    total_clientes = Cliente.objects.count()
    total_proveedores = Proveedor.objects.count()
    
    # Total compras y ventas del mes
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    compras_mes = Compra.objects.filter(
        fecha__gte=inicio_mes
    ).aggregate(
        total=Sum('costo_total'),
        cantidad=Sum('cantidad')
    )
    
    ventas_mes = Venta.objects.filter(
        fecha_creacion__gte=inicio_mes
    ).aggregate(
        total=Sum('precio'),
        cantidad=Sum('cantidad')
    )
    
    # Productos más vendidos (top 5)
    productos_mas_vendidos = Venta.objects.values(
        'id_producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum('precio')
    ).order_by('-total_vendido')[:5]
    
    context = {
        'total_productos': total_productos,
        'total_clientes': total_clientes,
        'total_proveedores': total_proveedores,
        'compras_mes': compras_mes['total'] or 0,
        'ventas_mes': ventas_mes['total'] or 0,
        'productos_mas_vendidos': productos_mas_vendidos,
    }
    
    return render(request, 'gestion/dashboard.html', context)

@login_required
def compra_list(request):
    search_query = request.GET.get('search', '')
    
    compras = Compra.objects.all().select_related('id_proveedor', 'id_producto')
    
    if search_query:
        compras = compras.filter(
            Q(numero_factura__icontains=search_query) |
            Q(id_proveedor__empresa__icontains=search_query) |
            Q(id_producto__nombre__icontains=search_query)
        )
    
    return render(request, 'gestion/compras/lista.html', {
        'compras': compras,
        'search_query': search_query
    })

@login_required
def compra_create(request):
    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Compra registrada exitosamente.')
            return redirect('compra_list')
    else:
        form = CompraForm()
    
    return render(request, 'gestion/compras/formulario.html', {'form': form})

@login_required
def compra_edit(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        if form.is_valid():
            form.save()
            messages.success(request, 'Compra actualizada exitosamente.')
            return redirect('compra_list')
    else:
        form = CompraForm(instance=compra)
    
    return render(request, 'gestion/compras/formulario.html', {'form': form})

@login_required
def compra_delete(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        compra.delete()
        messages.success(request, 'Compra eliminada exitosamente.')
        return redirect('compra_list')
    
    return render(request, 'gestion/compras/confirmar_eliminar.html', {'compra': compra})

@login_required
def venta_list(request):
    search_query = request.GET.get('search', '')
    
    ventas = Venta.objects.all().select_related('id_producto', 'id_cliente')
    
    if search_query:
        ventas = ventas.filter(
            Q(id_producto__nombre__icontains=search_query) |
            Q(id_cliente__nombre__icontains=search_query) |
            Q(id_cliente__apellido__icontains=search_query)
        )
    
    return render(request, 'gestion/ventas/lista.html', {
        'ventas': ventas,
        'search_query': search_query
    })

@login_required
def venta_create(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venta registrada exitosamente.')
            return redirect('venta_list')
    else:
        form = VentaForm()
    
    return render(request, 'gestion/ventas/formulario.html', {'form': form})

@login_required
def venta_edit(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venta actualizada exitosamente.')
            return redirect('venta_list')
    else:
        form = VentaForm(instance=venta)
    
    return render(request, 'gestion/ventas/formulario.html', {'form': form})

@login_required
def venta_delete(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.delete()
        messages.success(request, 'Venta eliminada exitosamente.')
        return redirect('venta_list')
    
    return render(request, 'gestion/ventas/confirmar_eliminar.html', {'venta': venta})

@login_required
def catalogo_view(request):
    # Vista principal del catálogo con pestañas
    clientes = Cliente.objects.all()
    productos = Producto.objects.all()
    proveedores = Proveedor.objects.all()
    
    context = {
        'clientes': clientes,
        'productos': productos,
        'proveedores': proveedores,
        'cliente_form': ClienteForm(),
        'producto_form': ProductoForm(),
        'proveedor_form': ProveedorForm(),
    }
    
    return render(request, 'gestion/catalogo/base_catalogo.html', context)

@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente agregado exitosamente.')
        else:
            messages.error(request, 'Error al agregar cliente.')
    
    return redirect('catalogo')

@login_required
def producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado exitosamente.')
        else:
            messages.error(request, 'Error al agregar producto.')
    
    return redirect('catalogo')

@login_required
def proveedor_create(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor agregado exitosamente.')
        else:
            messages.error(request, 'Error al agregar proveedor.')
    
    return redirect('catalogo')

@login_required
def inventario_list(request):
    # Obtener datos del inventario
    inventario = get_inventario_data()
    
    # Aplicar filtro de búsqueda
    search_query = request.GET.get('search', '')
    if search_query:
        inventario = [item for item in inventario 
                     if search_query.lower() in item['nombre'].lower() 
                     or search_query.lower() in item['marca'].lower()]
    
    # Aplicar filtro de stock
    stock_filter = request.GET.get('stock', '')
    if stock_filter:
        if stock_filter == 'critico':
            inventario = [item for item in inventario if item['stock_actual'] <= 2]
        elif stock_filter == 'bajo':
            inventario = [item for item in inventario if 3 <= item['stock_actual'] <= 5]
        elif stock_filter == 'agotado':
            inventario = [item for item in inventario if item['stock_actual'] <= 0]
        elif stock_filter == 'normal':
            inventario = [item for item in inventario if item['stock_actual'] > 5]
    
    # Aplicar ordenamiento
    sort_by = request.GET.get('sort', '')
    if sort_by:
        if sort_by == 'nombre':
            inventario.sort(key=lambda x: x['nombre'])
        elif sort_by == '-nombre':
            inventario.sort(key=lambda x: x['nombre'], reverse=True)
        elif sort_by == 'stock_actual':
            inventario.sort(key=lambda x: x['stock_actual'])
        elif sort_by == '-stock_actual':
            inventario.sort(key=lambda x: x['stock_actual'], reverse=True)
        elif sort_by == 'valor_total':
            inventario.sort(key=lambda x: x['valor_total'])
        elif sort_by == '-valor_total':
            inventario.sort(key=lambda x: x['valor_total'], reverse=True)
    
    # Obtener estadísticas
    estadisticas = get_estadisticas_inventario(inventario)
    
    context = {
        'inventario': inventario,
        'search_query': search_query,
        'stock_total': estadisticas['stock_total'],
        'valor_total': estadisticas['valor_total'],
        'productos_bajo_stock': estadisticas['productos_bajo_stock'],
        'productos_criticos': estadisticas['productos_criticos'],
        'productos_agotados': estadisticas['productos_agotados'],
        'ahora': timezone.now(),
    }
    
    return render(request, 'gestion/inventario/lista.html', context)

@login_required
def historial_precio_list(request):
    historial = HistorialPrecio.objects.all().select_related('id_producto')
    
    search_query = request.GET.get('search', '')
    if search_query:
        historial = historial.filter(
            Q(id_producto__nombre__icontains=search_query) |
            Q(id_producto__marca__icontains=search_query)
        )
    
    return render(request, 'gestion/historial_precios/lista.html', {
        'historial': historial,
        'search_query': search_query
    })

@login_required
def historial_precio_create(request):
    if request.method == 'POST':
        form = HistorialPrecioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Precio histórico agregado exitosamente.')
            return redirect('historial_precio_list')
    else:
        form = HistorialPrecioForm()
    
    return render(request, 'gestion/historial_precios/formulario.html', {'form': form})