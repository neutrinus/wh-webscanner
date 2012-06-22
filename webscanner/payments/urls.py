# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.views.decorators.csrf import csrf_exempt

urlpatterns = patterns('',
        url(r'^paypal/ret/$','gpayments.views.paypal_return', name='gpayments_paypal_return'),
        url(r'^paypal/cancel/$','gpayments.views.paypal_cancel', name='gpayments_paypal_cancel'),
        url(r'^change/$','gpayments.views.tariffs', name='gpayments_tariffs'),
        url(r'^buy/(\w+)/$', 'gpayments.views.buy', name='gpayments_buy'),
)

urlpatterns += patterns('',
    # xxx powinno być zmienione na url trudny do zgadnięcia!
    (r'^waeCai3chicohqu8uzoo/', include('paypal.standard.ipn.urls')),
) 

