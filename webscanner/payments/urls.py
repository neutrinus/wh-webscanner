# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.views.decorators.csrf import csrf_exempt

urlpatterns = patterns('payments.views',
        url(r'^paypal/ret/$','paypal_return', name='payments_paypal_return'),
        url(r'^paypal/cancel/$','paypal_cancel', name='payments_paypal_cancel'),
        url(r'^buy/$', 'buy', name='payments_buy'),
)

urlpatterns += patterns('',
    # xxx powinno być zmienione na url trudny do zgadnięcia!
    (r'^waeCai3chicohqu8uzoo/', include('paypal.standard.ipn.urls')),
)

