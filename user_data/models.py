from django.db import models


class UserData(models.Model):
    id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    user_name = models.CharField(max_length=100)

    def __str__(self):
        return super().__str__()
