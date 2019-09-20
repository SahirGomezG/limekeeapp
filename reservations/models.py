from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date
from django.urls import reverse
from django.db.models import Sum, F

# Create your models here.
class Reservations(models.Model):
    confirmation_code = models.CharField(max_length=12, primary_key=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE)
    guest = models.CharField(max_length=120)
    check_in = models.DateField(default=date.today)
    check_out = models.DateField(default=date.today)
    price = models.DecimalField(decimal_places=2, max_digits=1000)
    limekee_fee = models.DecimalField(decimal_places=2, max_digits=1000, blank=True, null=False, default=0)
    cleaning_fee = models.DecimalField (decimal_places=2, max_digits=1000, blank=True, null=False, default=0)
    total_due = models.DecimalField( decimal_places=2, max_digits=1000, default=0)
    notes = models.TextField(blank=True,null=False)
    paid = models.BooleanField(default=False)

    @property
    def total_due(self):
        return (self.limekee_fee + self.cleaning_fee)

    def total_due_for_stripe(self):
        return (self.limekee_fee + self.cleaning_fee )*100

    def __str__(self):
        return f'Reservation: {self.confirmation_code}'

    def get_absolute_url(self):
        return reverse("reservation-detail", kwargs={'confirmation_code':self.confirmation_code})

    class Meta:
        permissions = [
            ("create_reservation", "Can create new reservation"),
        ]
