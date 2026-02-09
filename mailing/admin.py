from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Client, Message, Mailing, MailingAttempt


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_time', 'end_time', 'status', 'message', 'clients_count', 'send_button')
    list_filter = ('status',)
    filter_horizontal = ('clients',)  # Удобный выбор клиентов

    def clients_count(self, obj):
        """Количество клиентов в рассылке"""
        return obj.clients.count()

    clients_count.short_description = 'Клиентов'

    def send_button(self, obj):
        """Кнопка для отправки рассылки"""
        url = reverse('send_mailing', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="background: #4CAF50; color: white; padding: 5px 10px; border-radius: 3px; text-decoration: none; margin-right: 5px;">📨 Отправить сейчас</a>',
            url
        )

    send_button.short_description = 'Действия'


# Остальные классы остаются без изменений
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'comment')
    search_fields = ('full_name', 'email')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'body')


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ('mailing', 'attempt_time', 'status', 'server_response')
    list_filter = ('status',)