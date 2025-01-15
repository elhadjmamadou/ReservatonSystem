from django.contrib import admin
from .models import Resource, Reservation
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name',)
    ordering = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'capacity', 'equipments', 'conditions', 'is_available')
        }),
    )

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('resource', 'user', 'start_time', 'end_time', 'status', 'is_waitlisted')
    list_filter = ('status', 'resource')
    search_fields = ('user__username', 'resource__name')
    ordering = ('start_time',)


admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)
