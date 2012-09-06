from django import forms
from captcha.fields import ReCaptchaField

class FormCaptcha(forms.Form):
    captcha = ReCaptchaField(attrs={'theme': 'white'})
