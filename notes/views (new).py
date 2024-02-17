from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect
# from django.urls import reverse
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

client = MongoClient("mongodb://localhost:27017/")
db = client['rough_notebook']
notes_collection = db['notes']



"""
print(request.session)
print(request.session.items())
print(type(request.session.items()))
"""


# Create your views here.

def handle_login(request):
    # take username and password from request.POST, if not found, take it from session database...
    username = request.POST.get("username", request.session.get("username", False))
    password = request.POST.get("password", request.session.get("password", False))
    print(f"authenticating using username={username} , password={password}")
    user = authenticate(request, username = username, password = password)
    if user is not None:
        login(request, user) # login successful, list notes
    else:
        pass # login failed, show error message (invalid credentials...)
    return HttpResponseRedirect("/")


def handle_logout(request):
    # show login page with "user logged out" message
    logout(request)
    return HttpResponseRedirect("/")

        
def list_notes(request):
    username = request.user.username
    notes = list(notes_collection.find({"username": username}).sort({"created": -1}))
    for i in notes:
        i["dateCreated"] = int(i["created"].timestamp()*1000) # for sorting and url purpose
        i["dateModified"] = int(i["modified"].timestamp()*1000) #for sorting purpose
        # timestamp() returning milliseconds part after decimal (to 3 places)
        # so *1000 to preserve it before converting to int
        i["modified"] = i["modified"].strftime("%d-%m-%Y %I:%M:%S %p")
        i["created"] = i["created"].strftime("%d-%m-%Y %I:%M:%S %p")
    return render(request, "list-notes-page.html", {"name": username, "notes": notes})


@cache_control(no_store = True)
def index(request):
    if request.user.is_authenticated:
    # if request.session.get("authentication_status", False) == "logged in":
        if request.method == "POST":
            # perform logout on logout form submission
            return handle_logout(request)
        else:
            # re-render list notes page on (refresh/reload)
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

    # validate first name
    if fname.isalpha() and len(fname)<30:
        request.session["fname"] = fname
    else:
        # show error message (invalid first name...)
        pass

    # validate last name
    if lname.isalpha() and len(lname)<30:
        request.session["lname"] = lname
    else:
        # show error message (invalid last name...)
        pass
    
    # validate email
    if fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email):
        request.session["email"] = email
    else:
        # show error message (invalid email...)
        print("\n\nregex email validation failed....")
        pass

    if User.objects.filter(email=email).exists():
        # show error message (user already exists...)
        print("\n\n\n\nemail already exists...")
        pass
    else:
        request.session["password"] = password2
    

    # validate username
    if not (5 <= len(username) <= 20):
        # show error message (username should have 5-20 characters...)
        pass
    
    if not username.isalnum():
        # show error message (invalid characters in username, should only contain letters and numbers and must not start with a number...)
        pass
    
    if not username[0].isalpha():
        # show error message (username must not start with a number...)
        pass

    if User.objects.filter(username=username).exists():
        # show error message (user already exists...)
        print("\n\n\n\nusername already exists...")
        pass
    else:
        request.session["username"] = username

    # validate password
    if not (5 <= len(password1) <= 20):
        # show error message (password should have 5-20 characters...)
        pass

    if password1 != password2:
        # show error message (passwords did not match...)
        print("password did not match...")
    

    # all the fields were valid, send OTP, ask user for OTP to verify email...
    request.session["otp"] = generate_and_send_otp(email)
    print("\n\nbefore redirecting to ask otp...")
    print(f"Email: {request.session.get('email')}, Username: {request.session.get('username')} Password: {request.session.get('password')}")
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
        username = request.POST["username"]
        # password1 = request.POST["password1"]
        # password2 = request.POST["password2"]
        # user = User.objects.create_user(username=username, password=password)
        # user.save()
        return redirect("login_view")
    else:
        #show signup page...
        return render(request, "forgot-password.html")








@login_required
@cache_control(no_store = True)
def new_note(request):
    print(request.user)
    if request.method=="POST":
        # save new note on form submission
        
        # current_time = datetime.now()
        # print("datetime.now()   =   ", datetime.now())
        
        current_time = timezone.now()
        print("timezone.now()   =   ", timezone.now())
        
        note={
            "username": request.user.username,
            "subject": request.POST["subject"],
            "modified": current_time,
            "content": request.POST["note-content"],
            "created": current_time,
        }
        notes_collection.insert_one(note)
        
        Note.objects.create(
            username = request.user,
            subject = request.POST["subject"],
            content = request.POST["note-content"],
            created = current_time,
            modified = current_time
        )
        
        return HttpResponseRedirect("/")
    else:
        return render(request, "new-note-page.html")


@login_required
@cache_control(no_store = True)
def view_note(request, created):
    username = request.user.username
    # fromtimestamp() does not take milliseconds precision as of now
    # created = datetime.fromtimestamp(int(created[:-3]))+timedelta(milliseconds=int(created[-3:]))
    # therefore using timedelta to add milliseconds after creating datetime object
    try:
        import pytz
        username = request.user
        created = datetime.fromtimestamp(int(created[:-3]), pytz.timezone("UTC"))
        print(created)
        s_note = Note.objects.get(username=username, created=created)
        print("s_note: ", s_note)
        note = list(notes_collection.find({"username": username, "created": created}))[0]
        print("note: ", note)
        note["modified"] = note["modified"].strftime("%d-%m-%Y %I:%M:%S %p")
        note["created"] = note["created"].strftime("%d-%m-%Y %I:%M:%S %p")
        return render(request, "view-note-page.html", {"name": username, "note": note})
    except Note.DoesNotExist:
        # note not found
        print("Note not found")
        return HttpResponseRedirect("/")
    except IndexError:
        #will throw a 'list index out of range' exception if not found
        # return a 404 page in this case.
        print("index error")
        return HttpResponseRedirect("/")




@login_required
@cache_control(no_store = True)
def edit_note(request, created):
    username = request.user.username
    created = datetime.fromtimestamp(int(created[:-3]))+timedelta(milliseconds=int(created[-3:]))
    try:
        note = list(notes_collection.find({"username": username, "created": created}))[0]
        note["modified"] = note["modified"].strftime("%d-%m-%Y %I:%M:%S %p")
        note["created"] = note["created"].strftime("%d-%m-%Y %I:%M:%S %p")
        return render(request, "edit-note-page.html", {"name": username, "note": note})
    except IndexError:
        #will throw a 'list index out of range' exception if not found
        # return a 404 page in this case.
        return HttpResponseRedirect("/")


@login_required
def update_note(request, created):
    username = request.user.username
    created = datetime.fromtimestamp(int(created[:-3]))+timedelta(milliseconds=int(created[-3:]))
    modified = datetime.now()
    subject = request.POST["subject"]
    content = request.POST["note-content"]
    notes_collection.update_one({"username": username, "created": created},
        {"$set" : {"subject": subject, "content": content, "modified": modified}})
    return HttpResponseRedirect("/")


@login_required
def delete_note(request, created):
    username = request.user.username
    created = datetime.fromtimestamp(int(created[:-3]))+timedelta(milliseconds=int(created[-3:]))
    notes_collection.delete_one({"username": username, "created": created})
    return HttpResponseRedirect("/")


