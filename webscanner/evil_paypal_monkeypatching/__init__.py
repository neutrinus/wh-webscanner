
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.forms import POSTBACK_ENDPOINT
from paypal.standard.forms import SANDBOX_POSTBACK_ENDPOINT
from django.utils.safestring import mark_safe

def _render_submit_button(self):
    return u'<button class="btn btn-large" name="submit">BUY NOW</button>'.format(paypal_image=self.get_image())

def render_form(self, endpoint, submit_button):
    return mark_safe(u"""<form action="{endpoint}" method="post">
        {items}
        {button}
        </form>
    """.format(endpoint=endpoint,
               items=self.as_p(),
               button=self._render_submit_button()))

def sandbox(self):
        return self.render_form(SANDBOX_POSTBACK_ENDPOINT)

def render(self):
        return self.render_form(POSTBACK_ENDPOINT)

PayPalPaymentsForm._render_submit_button = _render_submit_button
PayPalPaymentsForm.render_form = render_form
PayPalPaymentsForm.render = render
PayPalPaymentsForm.sandbox = sandbox

