from django.db.models.signals import post_syncdb

from django.contrib.auth.models import User

def new_create_superuser(app, created_models,**cos):
        import settings
        su_name=getattr(settings,'SUPERUSER','root')
        su_email=getattr(settings,'SUPERUSER_EMAIL','root@localhost.local')
        su_pass=getattr(settings,'SUPERUSER_PASSWORD','qqq')
        try:
            User.objects.get(username=su_name)
        except User.DoesNotExist:
            User.objects.create_superuser(su_name,su_email,su_pass)
            print "Created superuser (%s:%s)"%(su_name,su_pass)

post_syncdb.connect(new_create_superuser,sender=None)

