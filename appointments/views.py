from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from .models import Appointment, TimeSlot, SubscriptionPlan, UserSubscription, Payment, WorkoutSession, Exercise, ExerciseLog, UserProgress, PersonalBest, UserProfile, PaymentQRCode
from datetime import datetime, timedelta
from django.utils import timezone
import uuid
from .models import Certificate, Badge, Leaderboard
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Certificate, Badge, Leaderboard
from django.core.mail import EmailMessage
from django.db.models import Sum
from django.contrib.auth import login, logout, authenticate
from appointments.models import Contact
from django.core.files.storage import FileSystemStorage
from .otp_models import OTP
from .otp_views import send_otp_email
from .email_utils import send_subscription_email, send_appointment_email
from .forms import PaymentSubmissionForm

def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Login attempt - Username: {username}")  # Debug log
        
        user = authenticate(username=username, password=password)
        print(f"Authentication result: {'Success' if user is not None else 'Failed'}")  # Debug log
        
        if user is not None:
            if user.is_staff:  # Check if user is admin
                messages.error(request, 'Please use the admin interface to login as admin.')
                return render(request, 'appointments/login.html')
            
            login(request, user)
            print(f"User logged in successfully: {user.username}")  # Debug log
            messages.success(request, 'Successfully logged in!')
            return redirect('home')
        else:
            # Check if user exists but password is wrong
            if User.objects.filter(username=username).exists():
                print("User exists but authentication failed")  # Debug log
                messages.error(request, 'Invalid password')
            else:
                print("User does not exist")  # Debug log
                messages.error(request, 'Invalid username or password')
            return render(request, 'appointments/login.html')
    
    # Handle GET request
    if request.user.is_authenticated:
        if request.user.is_staff:  # If admin is logged in
            logout(request)  # Log them out
            request.session.flush()  # Clear all session data
            request.user = None
        return redirect('home')
    
    return render(request, 'appointments/login.html')


def user_logout(request):
    logout(request)  # Clears the current session
    request.session.flush()  # Clears all session data
    request.user = None  # Clears the user object
    return redirect('home')  # Redirect to home page


# View My Certificates
@login_required
def my_certificates(request):
    certificates = Certificate.objects.filter(user=request.user)
    return render(request, 'appointments/my_certificates.html', {'certificates': certificates})

# View My Badges
@login_required
def my_badges(request):
    badges = Badge.objects.filter(user=request.user)
    return render(request, 'appointments/my_badges.html', {'badges': badges})


# View for Personal Training
def personal_training(request):
    return render(request, 'appointments/personal_training.html')

# View for Yoga Classes
def yoga_classes(request):
    return render(request, 'appointments/yoga_classes.html')

# View for Strength Training
def strength_training(request):
    return render(request, 'appointments/strength_training.html')

# View for Steam and Sauna
def steam(request):
    return render(request, 'appointments/steam.html')

def nutrition(request):
    return render(request, 'appointments/nutrition.html')

def bmi(request):
    return render(request, 'appointments/bmi.html')



# View Leaderboard
def leaderboard(request):
    leaderboard_data = User.objects.annotate(total_points=Sum('badge__points')).order_by('-total_points')

    user_rank = None
    for index, user in enumerate(leaderboard_data, start=1):
        if user == request.user:
            user_rank = index
            break

    return render(request, 'appointments/leaderboard.html', {
        'leaderboard': leaderboard_data,
        'current_user': request.user,
        'user_rank': user_rank
        })
    #leaderboard_data = Leaderboard.objects.order_by('-points')
    #return render(request, 'appointments/leaderboard.html', {'leaderboard': leaderboard_data})
# Create your views here.

def home(request):
    # Check if user is admin and redirect to admin if they are
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)
        request.session.flush()
        request.user = None
        return redirect('home')
    
    context = {
        'subscription_plans': SubscriptionPlan.objects.all()
    }
    if request.user.is_authenticated:
        context['user_subscription'] = UserSubscription.objects.filter(
            user=request.user,
            is_active=True,
            end_date__gte=timezone.now().date()
        ).first()
    return render(request, 'appointments/home.html', context)

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        print(f"Registration attempt - Username: {username}, Email: {email}")  # Debug log
        
        # Validate all fields are present
        if not all([username, email, password1, password2]):
            messages.error(request, "All fields are required")
            return redirect('register')
        
        # Validate passwords match
        if password1 != password2:
            messages.error(request, "Passwords don't match")
            return redirect('register')
        
        # Validate password length
        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters long")
            return redirect('register')
        
        # Validate password contains both letters and numbers
        if not any(c.isalpha() for c in password1) or not any(c.isdigit() for c in password1):
            messages.error(request, "Password must contain both letters and numbers")
            return redirect('register')
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')
        
        # Check if email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('register')
        
        try:
            # Create user account
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            print(f"User created successfully: {user.username}")  # Debug log
            
            # Verify the user was created
            if User.objects.filter(username=username).exists():
                print("User exists in database after creation")  # Debug log
                
                # Try to authenticate the user
                auth_user = authenticate(username=username, password=password1)
                if auth_user is not None:
                    print("User authenticated successfully")  # Debug log
                    login(request, auth_user)
                    messages.success(request, 'Account created successfully!')
                    return redirect('home')
                else:
                    print("Authentication failed after user creation")  # Debug log
                    messages.error(request, 'Error during login. Please try logging in manually.')
                    return redirect('login')
            else:
                print("User not found in database after creation")  # Debug log
                messages.error(request, 'Error creating account. Please try again.')
                return redirect('register')
                
        except Exception as e:
            print(f"Error during user creation: {str(e)}")  # Debug log
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('register')
    
    return render(request, 'appointments/register.html')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Send OTP for password reset
            send_otp_email(email, 'password_reset')
            request.session['reset_email'] = email
            messages.success(request, 'OTP has been sent to your email')
            return redirect('verify_otp')
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email address')
    
    return render(request, 'forgot_password.html')

@login_required
def subscribe(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    time_slots = {
        'morning': TimeSlot.objects.get(session='morning'),
        'afternoon': TimeSlot.objects.get(session='afternoon'),
        'evening': TimeSlot.objects.get(session='evening'),
    }
    qr_codes = PaymentQRCode.objects.filter(is_active=True)

    if request.method == 'POST':
        time_slot_id = request.POST.get('time_slot')
        if not time_slot_id:
            messages.error(request, 'Please select a time slot')
            return redirect('subscribe', plan_id=plan_id)

        form = PaymentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.subscription_plan = plan
            payment.amount = plan.price
            payment.payment_status = 'pending'
            payment.save()

            time_slot = get_object_or_404(TimeSlot, id=time_slot_id)
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=30 * plan.duration_months)

            UserSubscription.objects.create(
                user=request.user,
                plan=plan,
                payment=payment,
                time_slot=time_slot,
                start_date=start_date,
                end_date=end_date,
                is_active=False
            )
            messages.info(request, 'Your payment is pending admin approval. You will be notified once your subscription is activated.')
            return redirect('my_appointments')
    else:
        form = PaymentSubmissionForm()

    return render(request, 'appointments/subscribe.html', {
        'plan': plan,
        'time_slots': time_slots,
        'qr_codes': qr_codes,
        'form': form
    })

@login_required
def book_appointment(request):
    # Check if user has active subscription
    subscription = UserSubscription.objects.filter(
        user=request.user,
        is_active=True,
        end_date__gte=timezone.now().date()
    ).first()
    
    if subscription:
        if request.method == 'POST':
            date = request.POST.get('date')
            time_slot_id = request.POST.get('time_slot')
            
            # Map time slot IDs to actual time ranges
            time_slot_mapping = {
                '1': {'start_time': '06:00:00', 'end_time': '10:00:00'},
                '2': {'start_time': '12:00:00', 'end_time': '16:00:00'},
                '3': {'start_time': '17:00:00', 'end_time': '21:00:00'}
            }
            
            if time_slot_id in time_slot_mapping:
                time_slot_data = time_slot_mapping[time_slot_id]
                # Convert string to time object
                start_time = datetime.strptime(time_slot_data['start_time'], '%H:%M:%S').time()
                end_time = datetime.strptime(time_slot_data['end_time'], '%H:%M:%S').time()
                # Check if appointment already exists for this date and user
                existing_appointment = Appointment.objects.filter(
                    user=request.user,
                    date=date
                ).first()
                
                if existing_appointment:
                    messages.error(request, 'You already have an appointment booked for this date.')
                    return redirect('book_appointment')
                
                appointment = Appointment.objects.create(
                    user=request.user,
                    user_subscription=subscription,
                    date=date,
                    time_slot=TimeSlot.objects.create(
                        start_time=start_time,
                        end_time=end_time,
                        is_available=True
                    ),
                    status='pending'
                )
                # Send appointment email
                send_appointment_email(request.user, appointment)
                messages.success(request, 'Appointment booked successfully!')
                return redirect('my_appointments')
            else:
                messages.error(request, 'Invalid time slot selected')
        
        return render(request, 'appointments/book.html', {
            'subscription': subscription,
            'today': timezone.now().date()
        })
    else:
        # Show subscription plans for non-subscribed users
        plans = SubscriptionPlan.objects.all()
        return render(request, 'appointments/book.html', {
            'subscription': None,
            'plans': plans,
            'show_subscription_packages': True  # Flag to show packages in the same format as home
        })

@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(
        user=request.user
    ).select_related('time_slot', 'user_subscription').order_by('date', 'time_slot__start_time')
    
    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments
    })

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    
    if appointment.status != 'cancelled':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
    else:
        messages.error(request, 'Appointment is already cancelled.')
    
    return redirect('my_appointments')

@login_required
def workout_log(request):
    if request.method == 'POST':
        # Create a new workout session
        appointment_id = request.POST.get('appointment')
        appointment = None
        if appointment_id:
            appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
        
        session = WorkoutSession.objects.create(
            user=request.user,
            notes=request.POST.get('notes', ''),
            appointment=appointment
        )
        
        # Process exercise logs
        exercises = request.POST.getlist('exercise')
        sets = request.POST.getlist('sets')
        reps = request.POST.getlist('reps')
        weights = request.POST.getlist('weight')
        durations = request.POST.getlist('duration')
        
        for i in range(len(exercises)):
            exercise = get_object_or_404(Exercise, id=exercises[i])
            ExerciseLog.objects.create(
                workout_session=session,
                exercise=exercise,
                sets=sets[i] if sets[i] else 0,
                reps=reps[i] if reps[i] else 0,
                weight=weights[i] if weights[i] else None,
                duration_minutes=durations[i] if durations[i] else None
            )
        
        messages.success(request, 'Workout logged successfully!')
        return redirect('workout_history')
    
    exercises = Exercise.objects.all()
    today_appointment = Appointment.objects.filter(
        user=request.user,
        date=timezone.now().date(),
        status='confirmed'
    ).first()
    
    return render(request, 'appointments/workout_log.html', {
        'exercises': exercises,
        'today_appointment': today_appointment
    })

@login_required
def workout_history(request):
    sessions = WorkoutSession.objects.filter(user=request.user).order_by('-date')
    return render(request, 'appointments/workout_history.html', {'sessions': sessions})

@login_required
def track_progress(request):
    if request.method == 'POST':
        UserProgress.objects.create(
            user=request.user,
            weight=request.POST.get('weight'),
            body_fat=request.POST.get('body_fat') or None,
            chest=request.POST.get('chest') or None,
            waist=request.POST.get('waist') or None,
            arms=request.POST.get('arms') or None,
            notes=request.POST.get('notes', '')
        )
        messages.success(request, 'Progress tracked successfully!')
        return redirect('progress_history')
    
    return render(request, 'appointments/track_progress.html')

@login_required
def progress_history(request):
    progress_entries = UserProgress.objects.filter(user=request.user)
    personal_bests = PersonalBest.objects.filter(user=request.user).select_related('exercise')
    
    # Calculate progress metrics
    if len(progress_entries) >= 2:
        latest = progress_entries[0]
        oldest = progress_entries.last()
        weight_change = latest.weight - oldest.weight
        
        if latest.body_fat and oldest.body_fat:
            fat_change = latest.body_fat - oldest.body_fat
        else:
            fat_change = None
    else:
        weight_change = None
        fat_change = None
    
    # Get exercise progress
    exercise_progress = {}
    for log in ExerciseLog.objects.filter(
        workout_session__user=request.user
    ).select_related('exercise'):
        if log.exercise.category == 'strength' and log.weight:
            if log.exercise.id not in exercise_progress:
                exercise_progress[log.exercise.id] = {
                    'name': log.exercise.name,
                    'weights': []
                }
            exercise_progress[log.exercise.id]['weights'].append(log.weight)
    
    # Update personal bests
    for log in ExerciseLog.objects.filter(workout_session__user=request.user):
        pb, created = PersonalBest.objects.get_or_create(
            user=request.user,
            exercise=log.exercise,
            defaults={
                'weight': log.weight,
                'reps': log.reps,
                'duration': log.duration_minutes
            }
        )
        
        if not created:
            if log.exercise.category == 'strength' and log.weight:
                if not pb.weight or log.weight > pb.weight:
                    pb.weight = log.weight
                    pb.reps = log.reps
                    pb.save()
            elif log.exercise.category == 'cardio' and log.duration_minutes:
                if not pb.duration or log.duration_minutes > pb.duration:
                    pb.duration = log.duration_minutes
                    pb.save()
    
    context = {
        'progress_entries': progress_entries,
        'personal_bests': personal_bests,
        'weight_change': weight_change,
        'fat_change': fat_change,
        'exercise_progress': exercise_progress.values()
    }
    return render(request, 'appointments/progress_history.html', context)


def generate_certificate(request, username):
    user = get_object_or_404(User, username=username)
    certificate_name = f"certificate_{user.username}.pdf"
    
    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{certificate_name}"'

    # Generate PDF content
    p = canvas.Canvas(response, pagesize=letter)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(200, 750, "Fitness Certification")
    p.setFont("Helvetica", 18)
    p.drawString(220, 700, f"Awarded to: {user.first_name} {user.last_name}")
    p.drawString(220, 670, "For completing the fitness course successfully")
    p.setFont("Helvetica", 12)
    p.drawString(220, 640, f"Date: {user.date_joined.strftime('%Y-%m-%d')}")
    p.showPage()
    p.save()

    # Save certificate in the database
    Certificate.objects.create(user=user, file=certificate_name)

    # Award Badge for Course Completion
    Badge.objects.create(user=user, badge_type='Course Completion')

    # Update Leaderboard
    leaderboard_entry, created = Leaderboard.objects.get_or_create(user=user)
    leaderboard_entry.points += 10  # Example: Add 10 points for course completion
    leaderboard_entry.save()

    # Email certificate
    email = EmailMessage(
        "Your Fitness Certificate",
        "Congratulations! Please find your certificate attached.",
        "admin@fitnesscenter.com",
        [user.email]
    )
    email.attach(certificate_name, response.getvalue(), 'application/pdf')
    email.send()

    return response


@login_required
def dashboard(request):
    user_appointments = Appointment.objects.filter(user=request.user)  # Only show current user's appointments
    return render(request, "dashboard.html", {"appointments": user_appointments})

def contact(request): 
    if request.method=="POST":
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        desc = request.POST['desc']
        #print(name, email, phone, desc)

        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        print("The data has been written to the db")
    #return HttpResponse("This is my homepage(/contact)")
    return render(request, 'appointments/contact.html')

from .models import NewsletterSignup 
from django.db import IntegrityError

def newsletter_signup(request):
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        message = request.POST['message']

        # Check if the email already exists
        if not NewsletterSignup.objects.filter(email=email).exists():
            newsletter_signup = NewsletterSignup(
                first_name=first_name,
                last_name=last_name,
                email=email,
                message=message
            )
            newsletter_signup.save()
            print("The data has been written to the db")
        else:
            print("Email already exists.")
            # You can show a friendly message in the template later

    return render(request, 'appointments/home.html')




def full_logout(request):
    logout(request)  # kills the session
    request.session.flush()  # clears all session data
    request.user = None   # clears the user object
    return redirect('home')  # redirect to home page

@login_required
def upload_photo(request):
    if request.method == 'POST':
        profile_photo = request.FILES.get('profile_photo')
        if profile_photo:
            # Get or create user profile
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # Delete old photo if exists
            if user_profile.profile_photo:
                user_profile.profile_photo.delete()
            
            # Save new photo
            user_profile.profile_photo = profile_photo
            user_profile.save()
            messages.success(request, 'Profile photo updated successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Please select a photo to upload.')
    
    return render(request, 'appointments/upload_photo.html')


