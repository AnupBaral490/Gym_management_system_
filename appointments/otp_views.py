from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .otp_models import OTP
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import SetPasswordForm

def send_otp_email(email, purpose):
    """Send OTP to user's email"""
    otp = OTP.generate_otp()
    OTP.objects.create(
        email=email,
        otp_code=otp,
        purpose=purpose
    )
    
    subject = f"Your OTP for {purpose.replace('_', ' ').title()}"
    message = f"Your OTP is: {otp}\nThis OTP is valid for 10 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL
    
    send_mail(subject, message, from_email, [email], fail_silently=False)

def request_otp(request):
    """Handle OTP request"""
    if request.method == 'POST':
        email = request.POST.get('email')
        purpose = request.POST.get('purpose')
        
        if purpose == 'registration' and User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('request_otp')
        
        send_otp_email(email, purpose)
        messages.success(request, 'OTP has been sent to your email.')
        return redirect('verify_otp')
    
    # Get email and purpose from URL parameters
    email = request.GET.get('email')
    purpose = request.GET.get('purpose')
    
    return render(request, 'request_otp.html', {
        'email': email,
        'purpose': purpose
    })

def verify_otp(request):
    """Verify OTP entered by user"""
    if request.method == 'POST':
        email = request.POST.get('email')
        otp_code = request.POST.get('otp')
        purpose = request.POST.get('purpose')
        
        try:
            otp_obj = OTP.objects.filter(
                email=email,
                otp_code=otp_code,
                purpose=purpose,
                is_verified=False
            ).latest('created_at')
            
            if otp_obj.is_expired():
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('request_otp')
            
            otp_obj.is_verified = True
            otp_obj.save()
            
            if purpose == 'registration':
                # Get registration data from session
                registration_data = request.session.get('registration_data')
                if registration_data:
                    # Create user account
                    user = User.objects.create_user(
                        username=registration_data['username'],
                        email=registration_data['email'],
                        password=registration_data['password']
                    )
                    login(request, user)
                    # Clear session data
                    del request.session['registration_data']
                    messages.success(request, 'Account created successfully!')
                    return redirect('home')
                else:
                    messages.error(request, 'Registration data not found. Please try registering again.')
                    return redirect('register')
            elif purpose == 'password_reset':
                # Store email in session for password reset
                request.session['reset_email'] = email
                return redirect('reset_password', email=email)
                
        except OTP.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')
    
    # Get email and purpose from session
    email = request.session.get('registration_data', {}).get('email') or request.session.get('reset_email')
    purpose = 'registration' if 'registration_data' in request.session else 'password_reset'
    
    return render(request, 'verify_otp.html', {
        'email': email,
        'purpose': purpose
    })

def reset_password(request, email):
    """Handle password reset"""
    # Verify that the email matches the one in session
    if email != request.session.get('reset_email'):
        messages.error(request, 'Invalid password reset request')
        return redirect('login')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, "Passwords don't match")
            return redirect('reset_password', email=email)
        
        try:
            user = User.objects.get(email=email)
            user.set_password(password1)
            user.save()
            
            # Clear session data
            del request.session['reset_email']
            
            messages.success(request, 'Password has been reset successfully! Please login with your new password.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'User not found')
            return redirect('login')
    
    return render(request, 'reset_password.html', {'email': email}) 