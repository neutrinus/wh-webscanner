from django.contrib.auth.models import User
from account.models import UserProfile
from datetime import datetime, timedelta as td
a = User.objects.filter(username="marek")[0]
b = UserProfile.objects.filter(user=a)[0]
b.paid_till_date = datetime.now() + td(weeks=1)
b.save()
