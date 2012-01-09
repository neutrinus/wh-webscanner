# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_list
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.db.models import Q
from django.contrib.comments.models import Comment
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.sitemaps import ping_google

from scanner.models import *

def index(request):
	#recipe_list = Recipe.objects.filter(is_deleted=False).order_by('-created_at')

	return render_to_response('index.html', {}, context_instance=RequestContext(request))



def results(request):
    
    test = Tests(domain="onet.pl")
    test.save()
    
    for testname in TESTDEF_PLUGINS:
        a = CommandQueue(test=test, testname = testname )
        a.save()

    
    
    #recipe_list = Recipe.objects.filter(is_deleted=False).order_by('-created_at')
    
    return render_to_response('results.html', {'test': test}, context_instance=RequestContext(request))
    

    
def check_new_results(request):
    return render_to_response('index.html', {}, context_instance=RequestContext(request))    
    
#@login_required
#def add_recipe(request):
	#units_list = Unit.objects.all()


	#if request.method == "POST":
		#form = RecipeForm(request.user, request.POST)
		#if form.is_valid():
			#recipe = form.save(commit=False)
			#recipe.author = request.user
			#recipe.creator_ip = request.META['REMOTE_ADDR']
			#recipe.permalink = slughifi.slughifi(form.cleaned_data['title'])
			#recipe.tags = recipe.tags.lower()

			#data = request.POST.copy()

			#recipe.save()
			#form.save_m2m()

			#for i in range(0, int(data['ingredients_count'])):
				#Food.objects.get_or_create(name= data['id_' + str(i) + '_namek'])

			#for i in range(0, int(data['ingredients_count'])):
				#foodk = Food.objects.get(name= data['id_' + str(i) + '_namek'])
				#unit = Unit.objects.get(name= data['id_' + str(i) + '_unit'])

				#if Ingredient.objects.filter(food=foodk, recipe=recipe, amount=float(data['id_' + str(i) + '_amount'].replace(",",".")) , unit=unit ).count() == 0:
					#m1 = Ingredient(food=foodk, recipe=recipe, amount=float(data['id_' + str(i) + '_amount'].replace(",",".")) , unit=unit )
					#m1.save()

			##sygnal odpowiedni
			#recipe_created.send(sender=Recipe, recipe=recipe)

			#request.user.message_set.create(message=_("Successfully saved recipe '%s'") % recipe.title)
			#return HttpResponseRedirect("/konto/przepisy/")
		#else:

			#return render_to_response("recipe/edit_recipe.html", {'form' : form, 'units_list': units_list}, context_instance=RequestContext(request))

	#else:
		#form = RecipeForm(initial={})

		#return render_to_response("recipe/edit_recipe.html", {'form' : form, 'units_list': units_list}, context_instance=RequestContext(request))


#@login_required
#def delete_recipe(request, permalink):
	#recipe = Recipe.objects.get(Q(permalink=permalink),Q(author=request.user))
	#recipe.is_deleted = True
	#recipe.save()

	#request.user.message_set.create(message=_("Successfully deleted recipe '%s'") % recipe.title)
	#return HttpResponseRedirect("/konto/przepisy/")

#@login_required
#def get_food(request, startswith):
	#food_list = Food.objects.filter(name__startswith=startswith)
	#return render_to_response('autocomplete_get_element.html', {'element_list': food_list},  mimetype="text/xml", context_instance=RequestContext(request))


#@login_required
#def rate_recipe(request, rate, user_name, permalink):
	#recipe = Recipe.objects.get(Q(permalink=permalink),Q(author__username__iexact=user_name))
	#recipe.rating.add(score=rate, user=request.user, ip_address=request.META['REMOTE_ADDR'])
	#return True

