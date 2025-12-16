from django.db import models
from django.contrib.auth.models import User


class Operacion(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    fecha = models.DateTimeField(auto_now_add=True)

    precio_compra = models.FloatField()
    precio_venta = models.FloatField()
    meses = models.FloatField()

    inversion_total = models.FloatField()
    beneficio_bruto = models.FloatField()

    beneficio_inversure = models.FloatField()
    beneficio_neto_inversure = models.FloatField()
    beneficio_participes = models.FloatField()

    rentabilidad_total = models.FloatField()
    rentabilidad_anualizada = models.FloatField()

    cumple_roi = models.BooleanField()

    precio_breakeven = models.FloatField()
    colchon_seguridad = models.FloatField()

    def __str__(self):
        return f"Operación {self.id} - {self.fecha.strftime('%d/%m/%Y')}"
