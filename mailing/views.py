from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib import messages
from .models import Client, Message, Mailing, MailingAttempt
from .forms import ClientForm, MessageForm


def home(request):
    """Главная страница со статистикой с кешированием"""
    cache_key = 'home_stats'
    cached_data = cache.get(cache_key)

    if cached_data is not None:
        total_mailings, active_mailings, unique_clients = cached_data
    else:
        total_mailings = Mailing.objects.count()
        now = timezone.now()
        active_mailings = Mailing.objects.filter(
            start_time__lte=now,
            end_time__gte=now
        ).count()
        unique_clients = Client.objects.distinct().count()
        cache.set(cache_key, (total_mailings, active_mailings, unique_clients), 300)

    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'unique_clients': unique_clients,
    }
    return render(request, 'mailing/home.html', context)


# Клиенты
@login_required
def client_list(request):
    clients = Client.objects.all().order_by('full_name')
    return render(request, 'mailing/client_list.html', {'clients': clients})


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'mailing/client_detail.html', {'client': client})


@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'mailing/client_form.html', {
        'form': form,
        'title': 'Создание нового клиента'
    })


@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'mailing/client_form.html', {
        'form': form,
        'title': f'Редактирование клиента: {client.full_name}'
    })


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        return redirect('client_list')
    return render(request, 'mailing/client_confirm_delete.html', {'client': client})


# Сообщения
@login_required
def message_list(request):
    messages = Message.objects.all().order_by('subject')
    return render(request, 'mailing/message_list.html', {'messages': messages})


@login_required
def message_detail(request, pk):
    message = get_object_or_404(Message, pk=pk)
    return render(request, 'mailing/message_detail.html', {'message': message})


@login_required
def message_create(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('message_list')
    else:
        form = MessageForm()
    return render(request, 'mailing/message_form.html', {
        'form': form,
        'title': 'Создание нового сообщения'
    })


@login_required
def message_update(request, pk):
    message = get_object_or_404(Message, pk=pk)
    if request.method == 'POST':
        form = MessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            return redirect('message_detail', pk=message.pk)
    else:
        form = MessageForm(instance=message)
    return render(request, 'mailing/message_form.html', {
        'form': form,
        'title': f'Редактирование сообщения: {message.subject}'
    })


@login_required
def message_delete(request, pk):
    message = get_object_or_404(Message, pk=pk)
    if request.method == 'POST':
        message.delete()
        return redirect('message_list')
    return render(request, 'mailing/message_confirm_delete.html', {'message': message})


# Отправка рассылки
@login_required
def send_mailing_now(request, pk):
    """Ручной запуск рассылки"""
    mailing = get_object_or_404(Mailing, pk=pk)


    now = timezone.now()
    if mailing.start_time <= now <= mailing.end_time:
        sent_count = 0
        failed_count = 0

        for client in mailing.clients.all():
            try:
                send_mail(
                    subject=mailing.message.subject,
                    message=mailing.message.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[client.email],
                    fail_silently=False,
                )
                # Запись успешной попытки
                MailingAttempt.objects.create(
                    mailing=mailing,
                    status='success',
                    server_response=f'Успешно отправлено клиенту {client.email}'
                )
                sent_count += 1
            except Exception as e:
                # Запись неудачной попытки
                MailingAttempt.objects.create(
                    mailing=mailing,
                    status='failed',
                    server_response=f'Ошибка: {str(e)}'
                )
                failed_count += 1

        if sent_count > 0:
            messages.success(
                request,
                f'✅ Рассылка отправлена! Успешно: {sent_count}, Неудачно: {failed_count}'
            )
        else:
            messages.warning(
                request,
                f'⚠️ Все отправки завершились с ошибкой. Неудачно: {failed_count}'
            )
    else:
        messages.error(
            request,
            '❌ Рассылка не может быть запущена: время рассылки неактивно'
        )

    return redirect('admin:mailing_mailing_changelist')


# Обработка ошибок
def custom_permission_denied(request, exception=None):
    """Кастомная страница для ошибки 403 (доступ запрещен)"""
    return render(request, 'mailing/access_denied.html', status=403)
