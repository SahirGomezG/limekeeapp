from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

from django.core.mail import send_mail

@receiver(post_save, sender = User)
def create_profile(sender, instance, created, **kwargs):
    if created: 
       Profile.objects.create(user=instance)
       send_mail(
                    'User Created!!',
                    f"Hey team, a new user has registered with us!\nLet's give {instance.username} a warm welcome.\n\nCheers!",
                    'sahir@limekee.com',
                    ['support@limekee.com'],
                    fail_silently=False,
                )

@receiver(post_save, sender = User)
def save_profile(sender,instance, **kwargs):
    instance.profile.save()
