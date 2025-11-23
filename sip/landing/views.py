from django.shortcuts import render
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

# Create your views here.
# landing/views.py


def landing_page(request):
    return render(request, 'landing/index.html')

def pricing_page(request):
    return render(request, 'landing/pricing.html')

@require_http_methods(["POST"])
def contact_form(request):
    try:
        data = json.loads(request.body)
        
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone', 'Not provided')
        company = data.get('company', 'Not provided')
        message = data.get('message', 'No message')
        plan = data.get('plan')
        
        # Email to you
        subject_to_dev = f'New Zephyr Pricing Inquiry - {plan} Plan'
        message_to_dev = f"""
New contact form submission:

Name: {name}
Email: {email}
Phone: {phone}
Company: {company}
Interested Plan: {plan}

Message:
{message}
"""
        
        send_mail(
            subject_to_dev,
            message_to_dev,
            'noreply@zephyr.com',  # From email
            ['ghimireshashank2004@gmail.com'],  # Your email
            fail_silently=False,
        )
        
        # Confirmation email to user
        subject_to_user = 'Thank you for contacting Zephyr'
        message_to_user = f"""
Hello {name},

Thank you for your interest in Zephyr's {plan} plan!

We have received your message and will get back to you shortly.

Best regards,
The Zephyr Team
"""
        
        send_mail(
            subject_to_user,
            message_to_user,
            'noreply@zephyr.com',
            [email],
            fail_silently=False,
        )
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)