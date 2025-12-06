from django.db.models import Sum, Avg, F, Subquery, OuterRef, Value, IntegerField, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import Producto, Compra, Venta, HistorialPrecio

def get_inventario_data():
    """
    Obtiene datos del inventario usando ORM de Django
    Versión corregida y optimizada
    """
    inventario = []
    
    try:
        # Obtener todos los productos
        productos = Producto.objects.all()
        
        for producto in productos:
            # Calcular total de compras para este producto
            total_compras = Compra.objects.filter(
                id_producto=producto
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            # Calcular total de ventas para este producto
            total_ventas = Venta.objects.filter(
                id_producto=producto
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            # Calcular costo promedio de compras
            costo_promedio = Compra.objects.filter(
                id_producto=producto
            ).aggregate(promedio=Avg('costo_unitario'))['promedio'] or 0
            
            # Obtener último precio histórico
            ultimo_precio = HistorialPrecio.objects.filter(
                id_producto=producto
            ).order_by('-fecha').first()
            
            # Calcular stock actual
            stock_actual = total_compras - total_ventas
            
            # Calcular valor total a costo
            valor_total = stock_actual * costo_promedio
            
            # Agregar al inventario
            inventario.append({
                'id_producto': producto.id_producto,
                'nombre': producto.nombre,
                'marca': producto.marca or '',
                'stock_inicial': 0,
                'total_compras': int(total_compras),
                'total_ventas': int(total_ventas),
                'stock_actual': int(stock_actual),
                'costo_promedio': float(costo_promedio),
                'precio_venta': float(ultimo_precio.precio_sugerido) if ultimo_precio else 0.0,
                'valor_total': float(valor_total),
                'ultima_actualizacion': producto.fecha_actualizacion
            })
        
        return inventario
        
    except Exception as e:
        print(f"Error en get_inventario_data: {e}")
        # En caso de error, retornar lista vacía
        return []

def get_inventario_producto(producto_id):
    """
    Obtiene datos de inventario para un producto específico
    """
    try:
        producto = Producto.objects.get(id_producto=producto_id)
        
        # Calcular total de compras
        total_compras = Compra.objects.filter(
            id_producto=producto_id
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        # Calcular total de ventas
        total_ventas = Venta.objects.filter(
            id_producto=producto_id
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        # Calcular costo promedio
        costo_promedio = Compra.objects.filter(
            id_producto=producto_id
        ).aggregate(promedio=Avg('costo_unitario'))['promedio'] or 0
        
        # Obtener último precio histórico
        ultimo_precio = HistorialPrecio.objects.filter(
            id_producto=producto_id
        ).order_by('-fecha').first()
        
        # Calcular stock actual
        stock_actual = total_compras - total_ventas
        
        return {
            'id_producto': producto.id_producto,
            'nombre': producto.nombre,
            'marca': producto.marca or '',
            'stock_inicial': 0,
            'total_compras': int(total_compras),
            'total_ventas': int(total_ventas),
            'stock_actual': int(stock_actual),
            'costo_promedio': float(costo_promedio),
            'precio_venta': float(ultimo_precio.precio_sugerido) if ultimo_precio else 0.0,
            'valor_total': float(stock_actual * costo_promedio),
            'ultima_actualizacion': producto.fecha_actualizacion
        }
        
    except Producto.DoesNotExist:
        return None
    except Exception as e:
        print(f"Error en get_inventario_producto: {e}")
        return None

def get_estadisticas_inventario(inventario_data=None):
    """
    Calcula estadísticas del inventario
    """
    if inventario_data is None:
        inventario_data = get_inventario_data()
    
    if not inventario_data:
        return {
            'stock_total': 0,
            'valor_total': 0.0,
            'productos_bajo_stock': 0,
            'productos_criticos': 0,
            'productos_agotados': 0,
            'valor_promedio_producto': 0.0
        }
    
    stock_total = sum(item.get('stock_actual', 0) for item in inventario_data)
    valor_total = sum(item.get('valor_total', 0.0) for item in inventario_data)
    productos_bajo_stock = sum(1 for item in inventario_data if item.get('stock_actual', 0) <= 5 and item.get('stock_actual', 0) > 0)
    productos_criticos = sum(1 for item in inventario_data if item.get('stock_actual', 0) <= 2 and item.get('stock_actual', 0) > 0)
    productos_agotados = sum(1 for item in inventario_data if item.get('stock_actual', 0) <= 0)
    
    valor_promedio = valor_total / len(inventario_data) if inventario_data else 0
    
    return {
        'stock_total': stock_total,
        'valor_total': valor_total,
        'productos_bajo_stock': productos_bajo_stock,
        'productos_criticos': productos_criticos,
        'productos_agotados': productos_agotados,
        'valor_promedio_producto': valor_promedio
    }