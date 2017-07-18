__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.core.management import call_command
from django.http import HttpResponse

from core import files, models as core_models, plugin_loader
from journal import models as journal_models, views as journal_views, forms as journal_forms
from press import models as press_models, forms
from security.decorators import press_only
from submission import models as submission_models


def index(request):
    if request.journal is not None:
        # if there's a journal, then we render the _journal_ homepage, not the press
        return journal_views.home(request)

    homepage_elements = core_models.HomepageElement.objects.filter(content_type=request.content_type,
                                                                   object_id=request.press.pk,
                                                                   active=True).order_by('sequence')

    template = "press/press_index.html"
    context = {
        'homepage_elements': homepage_elements,
    }

    # call all registered plugin block hooks to get relevant contexts
    for hook in settings.PLUGIN_HOOKS.get('yield_homepage_element_context', []):
        hook_module = plugin_loader.import_module(hook.get('module'))
        function = getattr(hook_module, hook.get('function'))
        element_context = function(request, homepage_elements)

        for k, v in element_context.items():
            context[k] = v

    return render(request, template, context)


def journals(request):
    template = "press/press_journals.html"

    journal_objects = journal_models.Journal.objects.filter(hide_from_press=False).order_by('sequence')

    context = {'journals': journal_objects}

    return render(request, template, context)


@staff_member_required
def manager_index(request):
    """
    This is an over-ride view that is returned by core_manager_index when there is no journal.
    :param request: django request
    :return: contextualised template
    """
    form = journal_forms.JournalForm()
    modal = None

    if request.POST:
        form = journal_forms.JournalForm(request.POST)
        modal = 'new_journal'
        if form.is_valid():
            new_journal = form.save()
            new_journal.sequence = request.press.next_journal_order()
            new_journal.save()
            call_command('sync_settings_to_journals', new_journal.code)
            call_command('sync_journals_to_sites')
            return redirect("{0}?journal={1}".format(reverse('core_edit_settings_group', kwargs={'group': 'journal'}),
                                                     new_journal.pk))

    template = 'press/press_manager_index.html'
    context = {
        'journals': journal_models.Journal.objects.all().order_by('sequence'),
        'form': form,
        'modal': modal,
        'published_articles': submission_models.Article.objects.filter(stage=submission_models.STAGE_PUBLISHED)[:50]
    }

    return render(request, template, context)


@staff_member_required
@press_only
def edit_press(request):
    """
    Staff members may edit the Press object.
    :param request: django request object
    :return: contextualised django template
    """

    press = request.press
    form = forms.PressForm(instance=press)

    if request.POST:
        form = forms.PressForm(request.POST, request.FILES, instance=press)
        if form.is_valid():
            form.save()

            if press.default_carousel_image:
                from core import logic as core_logic
                core_logic.resize_and_crop(press.default_carousel_image.path, [750, 324], 'middle')

            messages.add_message(request, messages.INFO, 'Press updated.')

            return redirect(reverse('core_manager_index'))

    template = 'press/edit_press.html'
    context = {
        'press': press,
        'form': form,
    }

    return render(request, template, context)


def serve_press_cover(request):
    p = press_models.Press.get_press(request)

    response = files.serve_press_cover(request, p)

    return response


@staff_member_required
def journal_order(request):
    """
    Takes a list of posted ids and sorts journals.
    :param request: request object
    :return: a json string
    """

    journals = journal_models.Journal.objects.all()

    ids = [int(_id) for _id in request.POST.getlist('journal[]')]

    for journal in journals:
        sequence = ids.index(journal.pk)
        journal.sequence = sequence
        journal.save()

    return HttpResponse('Thanks')
