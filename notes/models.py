from django.db import models
from django.conf import settings

# Create your models here.
class Note(models.Model):
    username = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.TextField()
    content = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()


    def is_viewer(self, username):
        # 'username' has explicit permission to view.
        try:
            return Share.objects.filter(created=self, username=username, access_type="view").exists()
        except TypeError:
            return False
    def can_view(self, username):
        # 'username' has explicit/implicit permission to view i.e. can view/edit/manage.
        # also return True if anyone with link can view (from self.username)
        try:
            return Share.objects.filter(created=self, username__in=(username, self.username)).exists()
        except TypeError:
            return False
    def get_viewers(self):
        return [s.username for s in Share.objects.filter(created=self, access_type="view")]


    def is_editor(self, username):
        # 'username' has explicit permission to edit.
        try:
            return Share.objects.filter(created=self, username=username, access_type="edit").exists()
        except TypeError:
            return False
    def can_edit(self, username):
        # has explicit/implicit permission to edit i.e. can edit/manage.
        # also return True if anyone with link can edit (from self.username)
        try:
            return Share.objects.filter(created=self, username__in=(username, self.username), access_type__in=("edit", "manage")).exists()
        except TypeError:
            return False
    def get_editors(self):
        return [s.username for s in Share.objects.filter(created=self, access_type="edit")]


    def is_manager(self, username):
        # 'username' has explicit permission to manage.
        try:
            return Share.objects.filter(created=self, username=username, access_type="manage").exists()
        except TypeError:
            return False
    def can_manage(self, username):
        # 'username' has explicit permission to manage AND also return True if anyone with link can manage (from self.username)
        try:
            return Share.objects.filter(created=self, username__in=(username, self.username), access_type="manage").exists()
        except TypeError:
            return False
    def get_managers(self):
        return [s.username for s in Share.objects.filter(created=self, access_type="manage")]

            
    def anyone_with_link_can(self, can=None):
        # [ "edit"==anyone_with_link_can() ] use this syntax to check if anyone with link is "editor" (explicitly)
        # [ anyone_with_link_can("edit") ] use this syntax to check if anyone with link can "edit" (implicitly) (has edit/manage permission)

        # explicitly return permission
        if can is None:
            try:
                return Share.objects.get(created=self, username=self.username).access_type
            except AttributeError:
                return None
        else:
            # implicit i.e. if has view/edit/manage permission then can view (implicitly)
            if can=="view":
                return Share.objects.filter(created=self, username=self.username).exists()
            elif can=="edit":
                return Share.objects.filter(created=self, username=self.username, access_type__in=("edit", "manage")).exists()
            elif can=="manage":
                return Share.objects.filter(created=self, username=self.username, access_type=can).exists()

    def __str__(self):
        return f"{self.username.first_name} ({self.username}) : {self.subject}"

ACCESS_CHOICES = (
    ("view", "View"),
    ("edit", "Edit"),
    ("manage", "Manage"),
)

class Share(models.Model):
    created = models.ForeignKey(Note, on_delete=models.CASCADE)
    username = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    access_type = models.CharField(max_length=6, choices=ACCESS_CHOICES)

    def __str__(self):
        return f"{self.created} ({self.username} - {self.access_type})"