from django.contrib import admin

from . import models


@admin.register(models.Model)
class ModelAdmin(admin.ModelAdmin):
    pass


class InstalledModelInlineAdmin(admin.TabularInline):
    model = models.InstalledModel
    readonly_fields = (
        "modified",
        "running",
    )


@admin.register(models.Backend)
class BackendAdmin(admin.ModelAdmin):
    list_filter = ("enabled",)
    inlines = (InstalledModelInlineAdmin,)


@admin.register(models.Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization",
        "enabled",
    )
    list_filter = ("enabled",)
    search_fields = ("id", "organization__name", "organization__short")
