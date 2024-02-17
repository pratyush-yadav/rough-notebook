from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect
# from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.cache import cache_control
from django.utils import timezone
from datetime import datetime, timedelta
from pymongo import MongoClient
from random import randint
from re import fullmatch
from django.core.mail import send_mail
from .models import Note, Share
import pytz
from django.forms.models import model_to_dict

client = MongoClient("mongodb://localhost:27017/")
db = client['rough_notebook']
notes_collection = db['notes']



"""
print(request.session)
print(request.session.items())
print(type(request.session.items()))
"""

email_exists = lambda email : User.objects.filter(email=email).exists()
username_exists = lambda username : User.objects.filter(username=username).exists()

# Create your views here.

def handle_login(request):
    # take username and password from request.POST, if not found, take it from session database (login after account creation)...
    username = request.POST.get("username", request.session.get("username", False))
    password = request.POST.get("password", request.session.get("password", False))
    # print(f"authenticating using username={username} , password={password}")
    user = authenticate(request, username = username, password = password)
    if user is not None:
        login(request, user) # login successful, list notes
    else:
        messages.error(request, "Login failed, invalid credentials...")
    return HttpResponseRedirect("/")


def handle_logout(request):
    logout(request)
    messages.info(request, "User logged out successfully...")
    return HttpResponseRedirect("/")

        
def list_notes(request):
    logged_in_user = request.user
    my_notes = Note.objects.filter(username=logged_in_user).values()
    for n in my_notes:
        n["dateCreated"] = int(n["created"].timestamp()*1000000) # for sorting and url purpose
        n["dateModified"] = int(n["modified"].timestamp()*1000000) #for sorting purpose
        # timestamp() returning milliseconds part after decimal (to 6 places)
        # so *1000000 to preserve it before converting to int
        n["modified"] = n["modified"].strftime("%d-%m-%Y %I:%M:%S %p") # for dispaly purpose
        n["created"] = n["created"].strftime("%d-%m-%Y %I:%M:%S %p") # for display purpose
        print(n)

    shared_notes = []
    share = Share.objects.filter(username=logged_in_user).select_related("created")
    for s in share:
        # type(logged_in_user) = <class 'django.utils.functional.SimpleLazyObject'>
        # type(s.created) = <class 'notes.models.Note'>
        # type(s.created.username) = <class 'django.contrib.auth.models.User'>
        # type(s.created.username.username) = <class 'str'>
        # type(logged_in_user.username) = <class 'str'>
        if s.created.username.username == logged_in_user.username:
            continue
        n = model_to_dict(s.created)
        # (s) was an instance of "Share" model, now (s.created / n) is aan instance of "Note" model.
        n["dateCreated"] = int(n["created"].timestamp()*1000000) # for sorting and url purpose
        n["dateModified"] = int(n["modified"].timestamp()*1000000) #for sorting purpose
        n["modified"] = n["modified"].strftime("%d-%m-%Y %I:%M:%S %p") # for dispaly purpose
        n["created"] = n["created"].strftime("%d-%m-%Y %I:%M:%S %p") # for display purpose
        shared_notes.append(n)
        print(n)
        
    try:
        load_after_save = request.session["load_after_save"]
        del request.session["load_after_save"]
    except KeyError:
        load_after_save = "false"
        # in JS, False is false (with small 'f')


    return render(request, "list-notes-page.html", {"name": logged_in_user, "notes": my_notes, "sharedNotes": shared_notes, "load_after_save": load_after_save})


@cache_control(no_store = True)
def index(request):
    if request.path == "/note/":
        # replace path from "/note/" to "/" (website root)
        return HttpResponseRedirect("/")
    if request.user.is_authenticated:
        if request.method == "POST":
            # perform logout on logout form submission
            return handle_logout(request)
        else:
            # render list notes page (re-render on refresh/reload)
            return list_notes(request)
    else:
        if request.method == "POST":
            # perform login on login form submission
            return handle_login(request)
        else:
            # initial site visit (show login page)
            return render(request, "login.html")



def generate_and_send_otp(email):
    otp = str(randint(1000, 9999))
    send_mail(
        "Rough Notebook",
        f"{otp} is your OTP for Rough Notebook.",
        "from@example.com",
        [email],
        fail_silently=False,
    )
    return otp


def validate_signup_form_and_send_otp(request):
    fname = request.POST["fname"]
    lname = request.POST["lname"]
    email = request.POST["email"]
    username = request.POST["username"]
    password1 = request.POST["password1"]
    password2 = request.POST["password2"]

    print("messages after validating everything: ", messages.get_messages(request))

    # validate first name
    if fname.isalpha() and len(fname)<30:
        request.session["fname"] = fname
    else:
        messages.error(request, "invalid first name...")

    # validate last name
    if lname.isalpha() and len(lname)<30:
        request.session["lname"] = lname
    else:
        messages.error(request, "invalid last name...")
    
    # validate email
    if fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email):
        request.session["email"] = email
    else:
        messages.error(request, "invalid email...")

    if email_exists(email):
        messages.error(request, "user already exists with this email...")
    else:
        request.session["password"] = password2
    
    # validate username
    if not (5 <= len(username) <= 20):
        messages.error(request, "username should have 5-20 characters...")
    
    if not username.isalnum():
        messages.error(request, "invalid characters in username, should only contain letters and numbers and must not start with a number...")
    
    if not username[0].isalpha():
        messages.error(request, "username must not start with a number...")

    if username_exists(username):
        messages.error(request, "user already exists with this username...")
    else:
        request.session["username"] = username

    # validate password
    if not (5 <= len(password1) <= 20):
        messages.error(request, "password should have 5-20 characters...")

    if password1 != password2:
        messages.error(request, "passwords did not match...")

    m = messages.get_messages(request)
    print("messages after validating everything: ", m)
    print(type(m))
    print(len(m))

    if len(messages.get_messages(request)) > 0:
        # some fields were invalid...
        request.session["form-invalid"] = True
    else:
        # all the fields were valid, send OTP, ask user for OTP to verify email...
        request.session["otp"] = generate_and_send_otp(email)

    return HttpResponseRedirect("")


def create_user(request):
    print("\ncreating user with...")
    print(f"Email: {request.session.get('email')}, Username: {request.session.get('username')} Password: {request.session.get('password')}")
    user = User.objects.create_user(
        username = request.session.get("username", ""),
        email = request.session.get("email", ""),
        first_name = request.session.get("fname", ""),
        last_name = request.session.get("lname", ""),
        password = request.session.get("password", "")
    )
    user.save()


def verify_otp_and_create_user(request):
    if request.POST["otp"] == request.session["otp"]:
        del request.session["otp"]
        # OTP verified...
        create_user(request)
        return handle_login(request)
    else:
        # show error message (incorrect OTP...)
        print("OTP incorrect...")
        return HttpResponseRedirect("")


@cache_control(no_store = True)
def signup_view(request):
    if request.method=="POST":
        if "email" in request.POST:
            return validate_signup_form_and_send_otp(request)
        elif "back" in request.POST:
            del request.session["otp"]
            return HttpResponseRedirect("")
        elif "verify-otp" in request.POST:
            return verify_otp_and_create_user(request)
    elif "form-invalid" in request.session:
        return render(request, "signup.html")
    elif "otp" in request.session:
        return render(request, "ask-otp.html")
    elif request.user.is_authenticated:
        # if user presses browser back button (on home page) after account creation,
        # redirecting to home page again instead of showing signup page...
        return HttpResponseRedirect("/")
    else:
        # normal signup_page visit or refresh...
        return render(request, "signup.html")






def forgot_password_view(request):
    if request.method=="POST":
        if "username" in request.POST:
            username_or_email = request.POST["username"]
            if username_exists(username_or_email):
                user = User.objects.get(username=username_or_email)
                email = user.email
            elif email_exists(username_or_email):
                user = User.objects.get(email=username_or_email)
                email = user.email
            else:
                messages.error(request, f"'{username_or_email}' is NOT a valid username or email !")
                return HttpResponseRedirect("")
            request.session["user"] = user.id
            request.session["otp"] = generate_and_send_otp(email)
            messages.success(request, "OTP sent to registered email ID...")
        elif "back" in request.POST:
            del request.session["otp"]
        elif "verify-otp" in request.POST:
            if request.POST["otp"] == request.session["otp"]:
                del request.session["otp"]
                request.session["ask-password"] = True
            else:
                messages.error(request, "Incorrect OTP !")
        elif "password2" in request.POST:
            password1 = request.POST["password1"]
            password2 = request.POST["password2"]
            if password1 == password2:
                user = User.objects.get(id=request.session["user"])
                user.set_password(password2)
                user.save()
                del request.session["ask-password"]
                print(password1)
                messages.success(request, "Password changed successfully...")
                return HttpResponseRedirect("/")
            messages.error(request, "passwords did not match...")
        return HttpResponseRedirect("")
    elif "otp" in request.session:
        return render(request, "ask-otp-2.html")
    elif "ask-password" in request.session:
        return render(request, "set-password.html")
    elif request.user.is_authenticated:
        # don't know
        # if user presses browser back button (on home page) after changing password,
        # redirecting to home page again instead of showing forgot password page...
        return HttpResponseRedirect("/")
    else:
        # normal forgot_password_page visit or refresh...
        return render(request, "forgot-password.html")
    









@cache_control(no_store = True)
def new_note(request):
    if request.user.is_authenticated:
        if request.method=="POST":
            # save new note on form submission
            current_time = timezone.now()
            Note.objects.create(
                username = request.user,
                subject = request.POST["subject"],
                content = request.POST["note-content"],
                created = current_time,
                modified = current_time
            )
            request.session["load_after_save"] = "true"
            # in JS, True is true (with small 't')
            messages.success(request, "Note created successfully...")
            return HttpResponseRedirect("/")
        else:
            return render(request, "new-note-page.html", {"name": request.user.username})
    else:
        messages.error(request, "You need to be logged in to create a note !")
        return HttpResponseRedirect("/")


@cache_control(no_store = True)
def view_note(request, created):
    logged_in_user = request.user
    created = datetime.fromtimestamp(int(created)/1000000, pytz.timezone("UTC"))
    # fromtimestamp(seconds.millisecondsmicroseconds)...
    try:
        note = Note.objects.get(created=created)
        note_owner = note.username
    except Note.DoesNotExist:
        # note not found, return a 404 page in this case.
        messages.error(request, "Note not found !")
        return HttpResponseRedirect("/")

    
    if request.user.is_authenticated:
        if logged_in_user == note_owner:
            # case 1: logged_in_user is owner of note
            access = "owner"
        elif any := Share.objects.filter(created=note, username=logged_in_user):
            # case 2: user is not owner but authorized to view/edit/manage
            access = any[0].access_type
        elif any := Share.objects.filter(created=note, username=note_owner): #public
            # case 3: note is public
            access = any[0].access_type
        else:
            messages.error(request, "You do not have permission to access this note...")
            return HttpResponseRedirect("/")
    else:
        # no user is logged in... only show note if it is public.
        if any := Share.objects.filter(created=note, username=note_owner): #public
            # case 3: show only if (note is public)
            access = any[0].access_type
        else:
            # anyone with link (anonymous user) does not have any permission.
            messages.error(request, "You do not have permission to access this note...")
            return HttpResponseRedirect("/")
    
    note=model_to_dict(note)
    note["owner"] = note_owner
    note["dateCreated"] = int(note["created"].timestamp()*1000000) # will be used in <form action=""...>
    note["modified"] = note["modified"].strftime("%d-%m-%Y %I:%M:%S %p")
    note["created"] = note["created"].strftime("%d-%m-%Y %I:%M:%S %p")
    show_note_owner = logged_in_user != note_owner
    return render(request, "view-note-page.html", {"name": str(logged_in_user), "note": note, "access": access, "show_note_owner": show_note_owner})


@cache_control(no_store = True)
def edit_note(request, created):
    logged_in_user = request.user
    created = datetime.fromtimestamp(int(created)/1000000, pytz.timezone("UTC"))
    try:
        # note = model_to_dict(Note.objects.get(created=created))
        note = Note.objects.get(created=created)
        note_owner = note.username
    except Note.DoesNotExist:
        # note not found, return a 404 page in this case.
        messages.error(request, "Note not found !")
        return HttpResponseRedirect("/")
    
    if not (logged_in_user==note_owner or note.can_edit(logged_in_user) or note.anyone_with_link_can("edit")):
        messages.error(request, "You do not have permission to edit this note...")
        return HttpResponseRedirect("/")
    
    note = model_to_dict(note)
    note["owner"] = note_owner
    note["modified"] = note["modified"].strftime("%d-%m-%Y %I:%M:%S %p")
    note["created"] = note["created"].strftime("%d-%m-%Y %I:%M:%S %p")
    show_note_owner = logged_in_user != note_owner
    return render(request, "edit-note-page.html", {"name": str(logged_in_user), "note": note, "show_note_owner": show_note_owner})


def update_note(request, created):
    logged_in_user = request.user
    created = datetime.fromtimestamp(int(created)/1000000, pytz.timezone("UTC"))
    note = Note.objects.get(created=created)
    note_owner = note.username
    if (request.user.is_authenticated and logged_in_user==note_owner) or note.can_edit(logged_in_user) or note.anyone_with_link_can("edit"):
        note.subject = request.POST["subject"]
        note.content = request.POST["note-content"]
        note.modified = timezone.now()
        note.save()
        messages.success(request, "Note updated successfully...")
    else:
        messages.error(request, "You do not have permission to edit this note !")
    return HttpResponseRedirect("/")


def delete_note(request, created):
    if request.user.is_authenticated:
        created = datetime.fromtimestamp(int(created)/1000000, pytz.timezone("UTC"))
        Note.objects.get(created=created).delete()
        messages.success(request, "Note deleted successfully...")
    else:
        messages.error(request, "You need to be logged in to delete a note !")
    return HttpResponseRedirect("/")


def add_share_permission(request, note):
    note_owner = note.username
    user_field = request.POST.get("user", False)
    role = request.POST.get("role", False)
    if request.POST.get("anyone", False):
        # give permission to anyone with link...
        if role == "view":
            Share.objects.filter(created=note, access_type="view").delete()
            Share.objects.filter(created=note, username=note_owner, access_type__in=["edit", "manage"]).delete()
        elif role == "edit":
            Share.objects.filter(created=note, access_type__in=["view", "edit"]).delete()
            Share.objects.filter(created=note, username=note_owner, access_type="manage").delete()
        elif role == "manage":
            Share.objects.filter(created=note).delete()
        Share.objects.create(
            created = note,
            username = note_owner,
            access_type = role
        )
        messages.success(request, f"Anyone with the link now has permission to '{role}'...")
    elif user_field and username_exists(user_field):
        # give permission to specific user(s)...
        if user_field == note_owner.username:
            # when user entered their own username...
            if request.user == note_owner:
                messages.warning(request, "You already have access to the notes you created...")
            else:
                messages.warning(request, "Note owners already have access to the notes they create...")
        elif Share.objects.filter(created=note, username=note_owner).exists():
            # if anyone with link already has permission, remove existing permission, then create a new one...
            if role == "view":
                Share.objects.filter(created=note, username=note_owner).delete()
            elif role == "edit":
                Share.objects.filter(created=note, username=note_owner, access_type__in=["edit", "manage"]).delete()
            elif role == "manage":
                Share.objects.filter(created=note, username=note_owner, access_type="manage").delete()
            Share.objects.create(
                created = note,
                username = User.objects.get(username=user_field),
                access_type = role
            )
            messages.success(request, f"{user_field} now has permission to '{role}'...")
        else:
            try:
                # update permission if user already has any permission...
                update_share_permission(note, user_field, role)
                messages.success(request, f"permission to user '{user_field}' changed to '{role}'...")
            except Share.DoesNotExist:
                # give permission if user does not already have any... (ideal situation.)
                Share.objects.create(
                    created = note,
                    username = User.objects.get(username=user_field),
                    access_type = role
                )
                messages.success(request, f"{user_field} now has permission to '{role}'...")
    else:
        messages.error(request, "Invalid Username...")

def update_share_permission(note, user_field, role):
    s = Share.objects.get(created=note, username=User.objects.get(username=user_field))
    s.access_type = role
    s.save()
    
def share_note(request, created):
    logged_in_user = request.user
    created = datetime.fromtimestamp(int(created)/1000000, pytz.timezone("UTC"))
    note = Note.objects.get(created=created)
    note_owner = note.username
    if request.method=="POST":
        if "add" in request.POST:
            add_share_permission(request, note)
        elif "remove" in request.POST:
            user_field = request.POST.get("username", False)
            Share.objects.get(created=note, username=User.objects.get(username=user_field)).delete()
            messages.success(request, f"Removed access from user '{user_field}'...")
        elif "update" in request.POST:
            user_field = request.POST.get("username", False)
            role = request.POST.get("updateRole", False)
            update_share_permission(note, user_field, role)
        else:
            print("none of the cases handled")
        return HttpResponseRedirect("")
    else:
        if logged_in_user==note_owner or note.can_manage(logged_in_user) or note.anyone_with_link_can("manage"):
            share = {"view": [], "edit": [], "manage": []}
            for s in Share.objects.filter(created=note).select_related("username"):
                if s.access_type == "view":
                    share["view"].append(s.username.username if s.username!=note_owner else "@anyone_with_link")
                elif s.access_type == "edit":
                    share["edit"].append(s.username.username if s.username!=note_owner else "@anyone_with_link")
                elif s.access_type == "manage":
                    share["manage"].append(s.username.username if s.username!=note_owner else "@anyone_with_link")
                    # "s.username" is user object and "s.username.username" is username field of user object
            show_note_owner = logged_in_user != note_owner
            return render(request, "share.html", {"name": str(logged_in_user), "share": share, "note_owner": note_owner.username, "show_note_owner": show_note_owner})
        else:
            messages.error(request, "You do not have permission to share this note !")
            return HttpResponseRedirect("/")

