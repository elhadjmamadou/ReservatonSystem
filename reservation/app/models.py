from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ImproperlyConfigured

class Resource(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    capacity = models.PositiveIntegerField()
    equipments = models.TextField(blank=True)  # Liste des équipements associés, peut-être sous forme de texte ou JSON
    conditions = models.TextField(blank=True)  # Conditions d'utilisation de la ressource
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[('Reserved', 'Reserved'), ('Canceled', 'Canceled')])
    is_waitlisted = models.BooleanField(default=False)

    @transaction.atomic
    def save(self, *args, **kwargs):
        overlapping_reservations = Reservation.objects.filter(
            resource=self.resource,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            status='Reserved'
        ).exclude(pk=self.pk)

        if overlapping_reservations.exists():
            self.is_waitlisted = True
        else:
            self.is_waitlisted = False

        super().save(*args, **kwargs)

        if self.is_waitlisted:
            self.notify_waitlisted()

    def delete(self, *args, **kwargs):
        waitlisted_reservations = Reservation.objects.filter(
        resource=self.resource,
        start_time=self.start_time,
        end_time=self.end_time,
        is_waitlisted=True
        )
        super().delete(*args, **kwargs)
        for reservation in waitlisted_reservations:
            reservation.notify_waitlist_fulfillment()


    def update_resource_availability(self):
        overlapping_reservations = Reservation.objects.filter(
            resource=self.resource,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            status='Reserved'
        ).exclude(pk=self.pk)

        # Si des réservations se chevauchent, la ressource est indisponible
        if overlapping_reservations.exists():
            self.resource.is_available = False
        else:
            self.resource.is_available = True
        self.resource.save()


    def clean(self):
        overlapping_reservations = Reservation.objects.filter(
            resource=self.resource,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            status='Reserved'
        ).exclude(pk=self.pk)

        if overlapping_reservations.exists():
            self.notify_conflict(overlapping_reservations)
            raise ValidationError("Ce créneau est déjà réservé. Veuillez en choisir un autre.")


    def send_notification(subject, message, recipient_list):
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=recipient_list,
                fail_silently=False,
            )
        except Exception as e:
            # Log ou traitement en cas d'échec
            print(f"Erreur lors de l'envoi de l'email : {str(e)}")


    def notify_conflict(self, conflicting_reservations):
        for reservation in conflicting_reservations:
            message = (
                f"Votre réservation pour {self.resource.name} entre {self.start_time} et {self.end_time} "
                f"entre en conflit avec une autre réservation."
            )
            send_notification("Conflit de réservation détecté", message, [reservation.user.email])

    def notify_waitlisted(self):
        message = (
            f"Votre réservation pour {self.resource.name} entre {self.start_time} et {self.end_time} "
            "a été placée en file d'attente."
        )
        send_notification("Réservation en attente", message, [self.user.email])


    def notify_waitlist_fulfillment(self):
        # Rechercher les utilisateurs en liste d'attente pour cette ressource et ce créneau
        waitlisted_reservations = Reservation.objects.filter(
            resource=self.resource,
            start_time=self.start_time,
            end_time=self.end_time,
            is_waitlisted=True
        )
        
        if waitlisted_reservations.exists():
            first_in_line = waitlisted_reservations.first()
            first_in_line.is_waitlisted = False
            first_in_line.save()

            # Notifier l'utilisateur que le créneau est désormais disponible
            send_mail(
                subject="Créneau libéré pour votre réservation",
                message=f"Un créneau pour {first_in_line.resource.name} entre {first_in_line.start_time} et {first_in_line.end_time} est désormais disponible.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[first_in_line.user.email],
                fail_silently=False,
            )
