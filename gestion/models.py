from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from decimal import Decimal

class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    marca = models.CharField(max_length=100, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return self.nombre

class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    empresa = models.CharField(max_length=200, unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    productos = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'proveedores'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return self.empresa

class Compra(models.Model):
    id_compra = models.AutoField(primary_key=True)
    numero_factura = models.CharField(max_length=50, unique=True)
    fecha = models.DateField()
    id_proveedor = models.ForeignKey(Proveedor, on_delete=models.RESTRICT, db_column='id_proveedor')
    id_producto = models.ForeignKey(Producto, on_delete=models.RESTRICT, db_column='id_producto')
    costo_total = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    porcentaje_ganancia = models.DecimalField(max_digits=5, decimal_places=2)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ganancia_unitaria = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ganancia_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'compras'
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'

    def save(self, *args, **kwargs):
        # Calcular campos automáticos
        if not self.costo_unitario and self.cantidad > 0:
            self.costo_unitario = self.costo_total / self.cantidad
        
        if self.costo_unitario and self.porcentaje_ganancia:
            self.precio = self.costo_unitario * (1 + self.porcentaje_ganancia / 100)
            self.ganancia_unitaria = self.precio - self.costo_unitario
            self.ganancia_total = self.ganancia_unitaria * self.cantidad
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Compra #{self.numero_factura} - {self.id_producto}"

class Venta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column='id_producto')
    id_cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_cliente')
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    cantidad = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Total Venta")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ventas'
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'

    def __str__(self):
        return f"Venta #{self.id_venta} - {self.id_producto}"
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente el total antes de guardar"""
        if self.precio and self.cantidad:
            self.total = self.precio * self.cantidad
        super().save(*args, **kwargs)
    
    @property
    def precio_unitario(self):
        """Propiedad para acceder al precio (ya es unitario)"""
        return self.precio

class HistorialPrecio(models.Model):
    id_precio = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column='id_producto')
    fecha = models.DateTimeField(default=timezone.now)
    precio_sugerido = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'historial_precios'
        verbose_name = 'Historial de Precio'
        verbose_name_plural = 'Historial de Precios'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.id_producto} - ${self.precio_sugerido} - {self.fecha.strftime('%Y-%m-%d')}"

#---------- Análisis de Ventas ------------
class AnalisisVenta(models.Model):
    fecha = models.DateField(unique=True, verbose_name="Fecha del análisis")
    total_ventas = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total de ventas del día")
    promedio_ganancia = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Promedio de ganancia (20%)")
    ahorro = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Ahorro (30% del promedio)")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analisis_ventas'
        verbose_name = 'Análisis de Venta'
        verbose_name_plural = 'Análisis de Ventas'
        ordering = ['-fecha']

    def __str__(self):
        return f"Análisis {self.fecha} - Total: C${self.total_ventas}"

# Función para actualizar análisis
def actualizar_analisis_fecha(fecha):
    """Función para calcular y actualizar el análisis de una fecha específica"""

    # Calcular total de ventas del día
    total_dia = Venta.objects.filter(
        fecha_creacion__date=fecha
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    # Calcular métricas
    promedio_ganancia = total_dia * Decimal('0.20')  # 20%
    ahorro = promedio_ganancia * Decimal('0.30')  # 30% del promedio
    
    # Crear o actualizar el registro
    AnalisisVenta.objects.update_or_create(
        fecha=fecha,
        defaults={
            'total_ventas': total_dia,
            'promedio_ganancia': promedio_ganancia,
            'ahorro': ahorro
        }
    )

@receiver(post_save, sender=Venta)
def actualizar_analisis_venta(sender, instance, **kwargs):
    """Actualizar el análisis del día cuando se crea/edita una venta"""
    fecha_venta = instance.fecha_creacion.date()
    hoy = timezone.now().date()
    
    # Solo actualizar si la venta es de hoy (o la fecha correspondiente)
    if fecha_venta <= hoy:
        actualizar_analisis_fecha(fecha_venta)