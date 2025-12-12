import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Max  
from django.utils import timezone
from django.urls import reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .models import *
from .forms import *
from .utils import get_inventario_data, get_estadisticas_inventario
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import TruncDate, Cast
from decimal import Decimal
from django.contrib.auth.models import User

# -------------------- Usuario Demo -------------------- #
def autenticar_usuario_demo(request):
    """Autentica automáticamente al usuario demo si las credenciales coinciden"""
    user_demo = os.environ.get('USER_DEMO')
    password_demo = os.environ.get('PASSWORD_DEMO')
    
    if not user_demo or not password_demo:
        return None  
    
    # Crear o obtener usuario demo    
    user, created = User.objects.get_or_create(
        username=user_demo,
        defaults={
            'email': f'{user_demo}@demo.com',
            'is_staff': False,
            'is_superuser': False
        }
    )
    
    if created:
        user.set_password(password_demo)
        user.save()
    
    return user

# -------------------- Paginación y Filtrado -------------------- #
def paginar_queryset(request, queryset, default_filas=10):
    search_query = request.GET.get('search', '')
    filas_por_pagina = request.GET.get('filas', default_filas)
    
    try:
        filas_por_pagina = int(filas_por_pagina)
    except ValueError:
        filas_por_pagina = default_filas

    paginator = Paginator(queryset, filas_por_pagina)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'filas_por_pagina': filas_por_pagina,
        'opciones_filas': [5, 10, 25, 50],
    }
    
    return context

def login_demo(request):
    """Vista especial para login automático demo"""
    user = autenticar_usuario_demo(request)
    
    if user:
        # Autenticar y loguear al usuario
        login(request, user)
        return redirect('Login Demo')  
    else:
        from django.http import HttpResponse
        return HttpResponse("Demo no configurado", status=500)


# -------------------- Registro y Dashboard -------------------- #
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
    total_productos = Producto.objects.count()
    total_clientes = Cliente.objects.count()
    total_proveedores = Proveedor.objects.count()
    
    inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Cálculo de compras del mes
    compras_mes = Compra.objects.filter(fecha__gte=inicio_mes).aggregate(
        total=Sum('costo_total'), cantidad=Sum('cantidad')
    )
    
    # Cálculo de ventas del mes 
    ventas_mes = Venta.objects.filter(fecha_creacion__gte=inicio_mes).aggregate(
        total=Sum('total'), 
        cantidad=Sum('cantidad')
    )
    
    # Productos más vendidos 
    productos_mas_vendidos = Venta.objects.filter(fecha_creacion__gte=inicio_mes).values(
        'id_producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum('total')  
    ).order_by('-total_vendido')[:5]
    
    # Últimas compras del mes para el dashboard
    ultimas_compras = Compra.objects.filter(fecha__gte=inicio_mes).select_related(
        'id_producto'
    ).order_by('-fecha')[:5]
    
    context = {
        'total_productos': total_productos,
        'total_clientes': total_clientes,
        'total_proveedores': total_proveedores,
        'compras_mes': compras_mes['total'] or 0,
        'ventas_mes': ventas_mes['total'] or 0,
        'productos_mas_vendidos': productos_mas_vendidos,
        'ultimas_compras': ultimas_compras,  # Agregar esto
    }
    
    return render(request, 'gestion/dashboard.html', context)

# -------------------- Compras -------------------- #
@login_required
def compra_list(request):
    compras_qs = Compra.objects.all().select_related('id_proveedor', 'id_producto').order_by('-fecha')

    if request.GET.get('search'):
        search_query = request.GET.get('search', '')
        compras_qs = compras_qs.filter(
            Q(numero_factura__icontains=search_query) |
            Q(id_proveedor__empresa__icontains=search_query) |
            Q(id_producto__nombre__icontains=search_query)
        )
    
    if request.method == 'POST' and 'delete' in request.POST:
        compra_id = request.POST.get('compra_id')
        if compra_id:
            compra = get_object_or_404(Compra, pk=compra_id)
            compra.delete()
            messages.success(request, 'Compra eliminada exitosamente.')
            return redirect('compra_list')
    
    # Manejar GET request para preparar eliminación
    action = request.GET.get('action', '')
    pk = request.GET.get('pk')
    compra_eliminar = None
    
    if action == 'delete' and pk:
        compra_eliminar = get_object_or_404(Compra, pk=pk)

    context = paginar_queryset(request, compras_qs, default_filas=10)
    context['compras'] = context.pop('page_obj')
    context['compra_eliminar'] = compra_eliminar
    context['action'] = action
    
    return render(request, 'gestion/compras/lista.html', context)

@login_required
def compra_create(request):
    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            
            # Cálculos automáticos
            if compra.cantidad and compra.costo_total:
                compra.costo_unitario = compra.costo_total / compra.cantidad
            if compra.costo_unitario and compra.porcentaje_ganancia:
                compra.ganancia_unitaria = compra.costo_unitario * (compra.porcentaje_ganancia / 100)
            if compra.ganancia_unitaria and compra.cantidad:
                compra.ganancia_total = compra.ganancia_unitaria * compra.cantidad
            if compra.costo_unitario and compra.ganancia_unitaria:
                compra.precio = compra.costo_unitario + compra.ganancia_unitaria

            compra.save()
            
            # Guardar en historial de precios 
            producto = compra.id_producto
            precio_sugerido = compra.precio
            
            HistorialPrecio.objects.create(
                id_producto=producto,
                precio_sugerido=precio_sugerido
            )
            
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
            compra = form.save(commit=False)
            
            # Recalcular
            if compra.cantidad and compra.costo_total:
                compra.costo_unitario = compra.costo_total / compra.cantidad
            if compra.costo_unitario and compra.porcentaje_ganancia:
                compra.ganancia_unitaria = compra.costo_unitario * (compra.porcentaje_ganancia / 100)
            if compra.ganancia_unitaria and compra.cantidad:
                compra.ganancia_total = compra.ganancia_unitaria * compra.cantidad
            if compra.costo_unitario and compra.ganancia_unitaria:
                compra.precio = compra.costo_unitario + compra.ganancia_unitaria

            compra.save()
            
            # Actualizar historial de precios 
            producto = compra.id_producto
            precio_sugerido = compra.precio
            
            HistorialPrecio.objects.create(
                id_producto=producto,
                precio_sugerido=precio_sugerido
            )
            
            messages.success(request, 'Compra actualizada exitosamente.')
            return redirect('compra_list')
    else:
        form = CompraForm(instance=compra)
    
    return render(request, 'gestion/compras/formulario.html', {'form': form})

# -------------------- Ventas -------------------- #
@login_required
def venta_list(request):
    ventas_qs = Venta.objects.select_related('id_producto', 'id_cliente').order_by('-fecha_creacion')

    if request.GET.get('search'):
        search_query = request.GET.get('search', '')
        ventas_qs = ventas_qs.filter(
            Q(id_producto__nombre__icontains=search_query) |
            Q(id_cliente__nombre__icontains=search_query) |
            Q(id_cliente__apellido__icontains=search_query)
        )
    
    # Manejar POST request para eliminar (desde modal)
    if request.method == 'POST' and 'delete' in request.POST:
        venta_id = request.POST.get('venta_id')
        if venta_id:
            venta = get_object_or_404(Venta, pk=venta_id)
            venta.delete()
            messages.success(request, 'Venta eliminada exitosamente.')
            return redirect('venta_list')
    
    # Manejar GET request para preparar eliminación
    action = request.GET.get('action', '')
    pk = request.GET.get('pk')
    venta_eliminar = None
    
    if action == 'delete' and pk:
        venta_eliminar = get_object_or_404(Venta, pk=pk)

    context = paginar_queryset(request, ventas_qs, default_filas=10)
    context['ventas'] = context.pop('page_obj')
    context['venta_eliminar'] = venta_eliminar
    context['action'] = action
    
    return render(request, 'gestion/ventas/lista.html', context)

@login_required
def venta_create(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            venta = form.save(commit=False)
            # El total se calculará automáticamente en el save() del modelo
            venta.save() 
            
            messages.success(request, 'Venta creada exitosamente.')
            return redirect('venta_list')
    else:
        form = VentaForm()

    # Precios recomendados por producto
    ultimos_precios = HistorialPrecio.objects.values('id_producto') \
        .annotate(ultima_fecha=Max('fecha'))

    precios_recomendados = {}
    for item in ultimos_precios:
        historial = HistorialPrecio.objects.get(
            id_producto=item['id_producto'],
            fecha=item['ultima_fecha']
        )
        precios_recomendados[item['id_producto']] = float(historial.precio_sugerido)

    # Últimas ventas
    ultimas_ventas = Venta.objects.select_related('id_producto').order_by('-id_venta')[:5]

    context = {
        'form': form,
        'precios_recomendados': precios_recomendados,
        'ultimas_ventas': ultimas_ventas,
    }

    return render(request, 'gestion/ventas/formulario.html', context)

@login_required
def venta_edit(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.save()
            
            messages.success(request, 'Venta actualizada exitosamente.')
            return redirect('venta_list')
        else:
            messages.error(request, 'Error al actualizar la venta. Revisa los datos.')
    else:
        form = VentaForm(instance=venta)
        
        # Precios recomendados para el formulario de edición
        ultimos_precios = HistorialPrecio.objects.values('id_producto') \
            .annotate(ultima_fecha=Max('fecha'))

        precios_recomendados = {}
        for item in ultimos_precios:
            historial = HistorialPrecio.objects.get(
                id_producto=item['id_producto'],
                fecha=item['ultima_fecha']
            )
            precios_recomendados[item['id_producto']] = float(historial.precio_sugerido)
    
    # Últimas ventas
    ultimas_ventas = Venta.objects.select_related('id_producto').order_by('-id_venta')[:5]
    
    context = {
        'form': form,
        'precios_recomendados': precios_recomendados,
        'ultimas_ventas': ultimas_ventas,
        'venta': venta,
    }
    
    return render(request, 'gestion/ventas/formulario.html', context)

# -------------------- Inventario -------------------- #
@login_required
def inventario_list(request):
    inventario = get_inventario_data()
    search_query = request.GET.get('search', '')
    
    # Filtrar por búsqueda
    if search_query:
        inventario = [
            i for i in inventario 
            if search_query.lower() in i['nombre'].lower() 
            or (i['marca'] and search_query.lower() in i['marca'].lower())
        ]
    
    # Filtrar por stock
    stock_filter = request.GET.get('stock', '')
    if stock_filter:
        if stock_filter == 'critico':
            inventario = [i for i in inventario if i['stock_actual'] <= 2]
        elif stock_filter == 'bajo':
            inventario = [i for i in inventario if 3 <= i['stock_actual'] <= 5]
        elif stock_filter == 'agotado':
            inventario = [i for i in inventario if i['stock_actual'] <= 0]
        elif stock_filter == 'normal':
            inventario = [i for i in inventario if i['stock_actual'] > 5]
    
    # Ordenar
    sort_by = request.GET.get('sort', '')
    if sort_by:
        reverse = sort_by.startswith('-')
        key = sort_by.lstrip('-')
        inventario.sort(key=lambda x: x.get(key, ''), reverse=reverse)
    else:
        # Orden por defecto por nombre
        inventario.sort(key=lambda x: x['nombre'].lower())
    
    # Configurar paginación
    filas_por_pagina = int(request.GET.get('filas', 10))
    paginator = Paginator(inventario, filas_por_pagina)
    
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    # Calcular estadísticas del inventario completo 
    estadisticas = get_estadisticas_inventario(inventario)
    
    context = {
        'inventario': page_obj.object_list, 
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'filas_por_pagina': filas_por_pagina,
        'stock_total': estadisticas['stock_total'],
        'valor_total': estadisticas['valor_total'],
        'productos_bajo_stock': estadisticas['productos_bajo_stock'],
        'productos_criticos': estadisticas['productos_criticos'],
        'productos_agotados': estadisticas['productos_agotados'],
        'ahora': timezone.now(),
        'opciones_filas': [5, 10, 20, 50, 100],  # Opciones para mostrar por página
    }
    return render(request, 'gestion/inventario/lista.html', context)

# -------------------- Historial de Precios -------------------- #
@login_required
def historial_precio_list(request):
    historial_qs = HistorialPrecio.objects.select_related('id_producto').all()

    if request.GET.get('search'):
        search_query = request.GET.get('search', '')
        historial_qs = historial_qs.filter(
            id_producto__nombre__icontains=search_query
        )

    historial_qs = historial_qs.order_by('id_producto', '-fecha')
    context = paginar_queryset(request, historial_qs, default_filas=10)
    context['historial'] = context.pop('page_obj')
    
    total_productos = Producto.objects.count()
    periodo = f"{timezone.now().strftime('%d/%m/%Y')}"
    
    context.update({
        'total_productos': total_productos,
        'periodo': periodo,
    })

    return render(request, 'gestion/historial_precios/lista.html', context)


# -------------------- Catálogo -------------------- #
@login_required
def catalogo_view(request):
    """Página principal del catálogo"""
    return render(request, 'gestion/catalogo/base_catalogo.html')



@login_required
def clientes_view(request):
    
    # Obtener parámetros
    action = request.GET.get('action', 'list')
    pk = request.GET.get('pk')
    search_query = request.GET.get('search', '')
    
    # Inicializar variables
    form = None
    cliente_editando = None
    cliente_eliminar = None
    tiene_ventas = False   
    mensaje_mostrado = False
    
    # Manejar POST requests (para crear/editar/eliminar)
    if request.method == 'POST':
        # Si es una eliminación
        if 'delete' in request.POST:
            cliente_id = request.POST.get('cliente_id')
            if cliente_id:
                cliente = get_object_or_404(Cliente, pk=cliente_id)
                
                # Verificar si el cliente tiene ventas asociadas
                ventas_asociadas = Venta.objects.filter(id_cliente=cliente).exists()
                if ventas_asociadas:
                    messages.error(request, f'No se puede eliminar el cliente "{cliente.nombre} {cliente.apellido}" porque tiene ventas asociadas. Primero elimine o modifique las ventas relacionadas.')
                else:
                    cliente.delete()
                    messages.success(request, 'Cliente eliminado exitosamente.')
                
                mensaje_mostrado = True
                
                # Redirigir a la lista después de eliminar
                redirect_url = reverse('clientes_view') + '?action=list'
                if search_query:
                    redirect_url += f'&search={search_query}'
                return redirect(redirect_url)
        
        # Si es una creación o edición
        else:
            # Determinar si es edición o creación basado en la presencia de pk
            if 'pk' in request.GET or 'cliente_id' in request.POST:
                if 'cliente_id' in request.POST:
                    pk = request.POST.get('cliente_id')
                elif 'pk' in request.GET:
                    pk = request.GET.get('pk')
                
                if pk:
                    cliente_editando = get_object_or_404(Cliente, pk=pk)
                    form = ClienteForm(request.POST, instance=cliente_editando)
                    action = 'edit'
                else:
                    form = ClienteForm(request.POST)
                    action = 'create'
            else:
                form = ClienteForm(request.POST)
                action = 'create'
            
            if form.is_valid():
                form.save()
                if action == 'edit':
                    messages.success(request, 'Cliente actualizado exitosamente.')
                else:
                    messages.success(request, 'Cliente creado exitosamente.')
                mensaje_mostrado = True
                
                # Redirigir a la lista después de guardar
                redirect_url = reverse('clientes_view') + '?action=list'
                if search_query:
                    redirect_url += f'&search={search_query}'
                return redirect(redirect_url)
            else:
                messages.error(request, 'Error al guardar el cliente. Por favor verifica los datos.')
                mensaje_mostrado = True
    
    # Manejar GET requests
    elif request.method == 'GET':
        if action == 'edit' and pk:
            # Preparar formulario de edición
            cliente_editando = get_object_or_404(Cliente, pk=pk)
            form = ClienteForm(instance=cliente_editando)
            
        elif action == 'delete' and pk:
            # Preparar confirmación de eliminación
            cliente_eliminar = get_object_or_404(Cliente, pk=pk)
            # Verificar si tiene ventas asociadas para mostrar advertencia
            if cliente_eliminar:
                tiene_ventas = Venta.objects.filter(id_cliente=cliente_eliminar).exists()
            
        elif action == 'create':
            # Preparar formulario vacío para creación
            form = ClienteForm()
    
    clientes_qs = Cliente.objects.all().order_by('-fecha_creacion')
    
    if search_query:
        clientes_qs = clientes_qs.filter(
            Q(nombre__icontains=search_query) |
            Q(apellido__icontains=search_query)
        )
    
    # Paginación
    filas_por_pagina = request.GET.get('filas', 10)
    try:
        filas_por_pagina = int(filas_por_pagina)
    except ValueError:
        filas_por_pagina = 10
    
    paginator = Paginator(clientes_qs, filas_por_pagina)
    page_number = request.GET.get('page', 1)
    
    try:
        clientes = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        clientes = paginator.page(1)
    
    # Si no hay formulario activo, crear uno vacío para el formulario principal
    if form is None:
        form = ClienteForm()
    
    context = {
        'action': action,
        'search_query': search_query,
        'clientes': clientes,
        'cliente_form': form,
        'cliente_editando': cliente_editando,
        'cliente_eliminar': cliente_eliminar,
        'tiene_ventas': tiene_ventas,
        'filas_por_pagina': filas_por_pagina,
        'opciones_filas': [5, 10, 25, 50],
        'mensaje_mostrado': mensaje_mostrado,
    }
    
    return render(request, 'gestion/catalogo/clientes.html', context)


@login_required
def productos_view(request):
    """Todo de productos en un solo template"""
    action = request.GET.get('action', 'list')
    pk = request.GET.get('pk')
    search_query = request.GET.get('search', '')
    
    # Inicializar variables
    form = None
    producto_editando = None
    producto_eliminar = None
    tiene_ventas = False  
    tiene_compras = False  
    mensaje_mostrado = False
    
    # Manejar POST requests (para crear/editar/eliminar)
    if request.method == 'POST':
        # Si es una eliminación
        if 'delete' in request.POST:
            producto_id = request.POST.get('producto_id')
            if producto_id:
                producto = get_object_or_404(Producto, pk=producto_id)
                
                # Verificar si el producto tiene ventas asociadas
                ventas_asociadas = Venta.objects.filter(id_producto=producto).exists()
                # Verificar si el producto tiene compras asociadas
                compras_asociadas = Compra.objects.filter(id_producto=producto).exists()
                
                if ventas_asociadas or compras_asociadas:
                    mensaje_error = f'No se puede eliminar el producto "{producto.nombre}" porque tiene '
                    if ventas_asociadas and compras_asociadas:
                        mensaje_error += 'ventas y compras asociadas.'
                    elif ventas_asociadas:
                        mensaje_error += 'ventas asociadas.'
                    else:
                        mensaje_error += 'compras asociadas.'
                    mensaje_error += ' Primero elimine o modifique los registros relacionados.'
                    
                    messages.error(request, mensaje_error)
                else:
                    producto.delete()
                    messages.success(request, 'Producto eliminado exitosamente.')
                
                mensaje_mostrado = True
                
                # Redirigir a la lista después de eliminar
                redirect_url = reverse('productos_view') + '?action=list'
                if search_query:
                    redirect_url += f'&search={search_query}'
                return redirect(redirect_url)
        
        # Si es una creación o edición
        else:
            # Determinar si es edición o creación basado en la presencia de pk
            if 'pk' in request.GET or 'producto_id' in request.POST:
                if 'producto_id' in request.POST:
                    pk = request.POST.get('producto_id')
                elif 'pk' in request.GET:
                    pk = request.GET.get('pk')
                
                if pk:
                    producto_editando = get_object_or_404(Producto, pk=pk)
                    form = ProductoForm(request.POST, instance=producto_editando)
                    action = 'edit'
                else:
                    form = ProductoForm(request.POST)
                    action = 'create'
            else:
                form = ProductoForm(request.POST)
                action = 'create'
            
            if form.is_valid():
                form.save()
                if action == 'edit':
                    messages.success(request, 'Producto actualizado exitosamente.')
                else:
                    messages.success(request, 'Producto creado exitosamente.')
                mensaje_mostrado = True
                
                # Redirigir a la lista después de guardar
                redirect_url = reverse('productos_view') + '?action=list'
                if search_query:
                    redirect_url += f'&search={search_query}'
                return redirect(redirect_url)
            else:
                messages.error(request, 'Error al guardar el producto. Por favor verifica los datos.')
                mensaje_mostrado = True
    
    # Manejar GET requests
    elif request.method == 'GET':
        if action == 'edit' and pk:
            # Preparar formulario de edición
            producto_editando = get_object_or_404(Producto, pk=pk)
            form = ProductoForm(instance=producto_editando)
            
        elif action == 'delete' and pk:
            # Preparar confirmación de eliminación
            producto_eliminar = get_object_or_404(Producto, pk=pk)
            # Verificar si tiene registros asociados para mostrar advertencia
            if producto_eliminar:
                tiene_ventas = Venta.objects.filter(id_producto=producto_eliminar).exists()
                tiene_compras = Compra.objects.filter(id_producto=producto_eliminar).exists()
            
        elif action == 'create':
            # Preparar formulario vacío para creación
            form = ProductoForm()
    
    productos_qs = Producto.objects.all().order_by('-fecha_creacion')
    
    if search_query:
        productos_qs = productos_qs.filter(
            Q(nombre__icontains=search_query) |
            Q(marca__icontains=search_query) |
            Q(categoria__icontains=search_query)
        )
    
    # Paginación
    filas_por_pagina = request.GET.get('filas', 10)
    try:
        filas_por_pagina = int(filas_por_pagina)
    except ValueError:
        filas_por_pagina = 10
    
    paginator = Paginator(productos_qs, filas_por_pagina)
    page_number = request.GET.get('page', 1)
    
    try:
        productos = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        productos = paginator.page(1)
    
    # Si no hay formulario activo, crear uno vacío para el formulario principal
    if form is None:
        form = ProductoForm()
    
    context = {
        'action': action,
        'search_query': search_query,
        'productos': productos,
        'producto_form': form,
        'producto_editando': producto_editando,
        'producto_eliminar': producto_eliminar,
        'tiene_ventas': tiene_ventas,
        'tiene_compras': tiene_compras,
        'filas_por_pagina': filas_por_pagina,
        'opciones_filas': [5, 10, 25, 50],
        'mensaje_mostrado': mensaje_mostrado,
    }
    
    return render(request, 'gestion/catalogo/productos.html', context)


@login_required
def proveedores_view(request):
    action = request.GET.get('action', 'list')
    pk = request.GET.get('pk')
    search_query = request.GET.get('search', '')
    
    # Inicializar variables
    form = None
    proveedor_editando = None
    proveedor_eliminar = None
    tiene_compras = False   
    mensaje_mostrado = False
    
    # Manejar POST requests (para crear/editar/eliminar)
    if request.method == 'POST':
        # Si es una eliminación
        if 'delete' in request.POST:
            proveedor_id = request.POST.get('proveedor_id')
            if proveedor_id:
                proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
                
                # Verificar si el proveedor tiene compras asociadas
                compras_asociadas = Compra.objects.filter(id_proveedor=proveedor).exists()
                if compras_asociadas:
                    messages.error(request, f'No se puede eliminar el proveedor "{proveedor.empresa}" porque tiene compras asociadas. Primero elimine o modifique las compras relacionadas.')
                else:
                    proveedor.delete()
                    messages.success(request, 'Proveedor eliminado exitosamente.')
                
                mensaje_mostrado = True
                
                # Redirigir a la lista después de eliminar
                redirect_url = reverse('proveedores_view') + '?action=list'
                if search_query:
                    redirect_url += f'&search={search_query}'
                return redirect(redirect_url)
        
        # Si es una creación o edición
        else:
            # Determinar si es edición o creación basado en la presencia de pk
            if 'pk' in request.GET or 'proveedor_id' in request.POST:
                if 'proveedor_id' in request.POST:
                    pk = request.POST.get('proveedor_id')
                elif 'pk' in request.GET:
                    pk = request.GET.get('pk')
                
                if pk:
                    proveedor_editando = get_object_or_404(Proveedor, pk=pk)
                    form = ProveedorForm(request.POST, instance=proveedor_editando)
                    action = 'edit'
                else:
                    form = ProveedorForm(request.POST)
                    action = 'create'
            else:
                form = ProveedorForm(request.POST)
                action = 'create'
            
            if form.is_valid():
                form.save()
                if action == 'edit':
                    messages.success(request, 'Proveedor actualizado exitosamente.')
                else:
                    messages.success(request, 'Proveedor creado exitosamente.')
                mensaje_mostrado = True
                
                # Redirigir a la lista después de guardar
                redirect_url = reverse('proveedores_view') + '?action=list'
                if search_query:
                    redirect_url += f'&search={search_query}'
                return redirect(redirect_url)
            else:
                messages.error(request, 'Error al guardar el proveedor. Por favor verifica los datos.')
                mensaje_mostrado = True
    
    # Manejar GET requests
    elif request.method == 'GET':
        if action == 'edit' and pk:
            # Preparar formulario de edición
            proveedor_editando = get_object_or_404(Proveedor, pk=pk)
            form = ProveedorForm(instance=proveedor_editando)
            
        elif action == 'delete' and pk:
            # Preparar confirmación de eliminación
            proveedor_eliminar = get_object_or_404(Proveedor, pk=pk)
            # Verificar si tiene compras asociadas para mostrar advertencia
            if proveedor_eliminar:
                tiene_compras = Compra.objects.filter(id_proveedor=proveedor_eliminar).exists()
            
        elif action == 'create':
            # Preparar formulario vacío para creación
            form = ProveedorForm()
    
     
    proveedores_qs = Proveedor.objects.all().order_by('-fecha_creacion')
    
    if search_query:
        proveedores_qs = proveedores_qs.filter(
            Q(empresa__icontains=search_query) |
            Q(contacto__icontains=search_query) |
            Q(productos__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Paginación
    filas_por_pagina = request.GET.get('filas', 10)
    try:
        filas_por_pagina = int(filas_por_pagina)
    except ValueError:
        filas_por_pagina = 10
    
    paginator = Paginator(proveedores_qs, filas_por_pagina)
    page_number = request.GET.get('page', 1)
    
    try:
        proveedores = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        proveedores = paginator.page(1)
    
    # Si no hay formulario activo, crear uno vacío para el formulario principal
    if form is None:
        form = ProveedorForm()
    
    context = {
        'action': action,
        'search_query': search_query,
        'proveedores': proveedores,
        'proveedor_form': form,
        'proveedor_editando': proveedor_editando,
        'proveedor_eliminar': proveedor_eliminar,
        'tiene_compras': tiene_compras,
        'filas_por_pagina': filas_por_pagina,
        'opciones_filas': [5, 10, 25, 50],
        'mensaje_mostrado': mensaje_mostrado,
    }
    
    return render(request, 'gestion/catalogo/proveedores.html', context)


# -------------------- Análisis de Ventas -------------------- #
@login_required
def analisis_ventas_list(request):
    # Obtener filtros del formulario
    form = AnalisisVentaFilterForm(request.GET or None)
    
    # Consulta base
    analisis_qs = AnalisisVenta.objects.all()
    
    # Aplicar filtros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    search_query = request.GET.get('search', '')
    
    if fecha_inicio:
        try:
            analisis_qs = analisis_qs.filter(fecha__gte=fecha_inicio)
        except:
            pass
    
    if fecha_fin:
        try:
            analisis_qs = analisis_qs.filter(fecha__lte=fecha_fin)
        except:
            pass
    
    # Búsqueda por fecha (formato YYYY-MM-DD)
    if search_query:
        analisis_qs = analisis_qs.filter(
            Q(fecha__icontains=search_query)
        )
    
    # Ordenar por fecha descendente
    analisis_qs = analisis_qs.order_by('-fecha')
    
    # Calcular totales generales
    total_general = analisis_qs.aggregate(
        total_ventas=Sum('total_ventas'),
        total_ganancia=Sum('promedio_ganancia'),
        total_ahorro=Sum('ahorro')
    )
    
    # Manejar solicitudes para recalcular análisis
    if request.method == 'POST' and 'recalcular' in request.POST:
        fecha_str = request.POST.get('fecha')
        if fecha_str:
            try:
                from datetime import datetime
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                actualizar_analisis_fecha(fecha)
                messages.success(request, f'Análisis para {fecha} recalculado exitosamente.')
            except Exception as e:
                messages.error(request, f'Error al recalcular: {str(e)}')
            return redirect(f"{request.path}?{request.GET.urlencode()}")
    
    # Paginación
    context = paginar_queryset(request, analisis_qs, default_filas=10)
    context['analisis_list'] = context.pop('page_obj')
    context['form'] = form
    context['search_query'] = search_query
    context['total_general'] = total_general
    
    # Agregar los parámetros de filtro al contexto para mantenerlos en la paginación
    if fecha_inicio:
        context['fecha_inicio'] = fecha_inicio
    if fecha_fin:
        context['fecha_fin'] = fecha_fin
    
    return render(request, 'gestion/analisis_ventas/lista.html', context)

@login_required
def analisis_ventas_recalcular_todo(request):
    """Vista para recalcular todo el histórico"""
    if request.method == 'POST':
        # Obtener todas las fechas únicas de ventas
        from django.db.models import Count
        
        fechas_ventas = Venta.objects.annotate(
            fecha_venta=TruncDate('fecha_creacion')
        ).values('fecha_venta').annotate(
            total=Count('id_venta')
        ).order_by('fecha_venta')
        
        total_recalculado = 0
        for item in fechas_ventas:
            actualizar_analisis_fecha(item['fecha_venta'])
            total_recalculado += 1
        
        messages.success(request, f'{total_recalculado} días recalculados exitosamente.')
        return redirect('analisis_ventas_list')
    
    return render(request, 'gestion/analisis_ventas/recalcular.html')