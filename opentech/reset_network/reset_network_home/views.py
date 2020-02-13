from django.http import HttpResponseRedirect


def redirect_apply_root(request):
    return HttpResponseRedirect('/')
