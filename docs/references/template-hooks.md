# TemplateHook

Adding a hook-point in `main_app`'s template:


    # my_main_app/templates/_base.html

    { % load hooks_tags %}

    <!DOCTYPE html>
    <html>
      <head>
        …

        { % hook 'within_head' %}

        …
      </head>
    </html>

**Tip**

Here we are adding a *hook-point* called `within_head` where
*third-party* apps will be able to insert their code.

Creating a hook listener in a `third_party_app`:

    # third_party_app/template_hooks.py

    from django.template.loader import render_to_string
    from django.utils.html import mark_safe, format_html


    # Example 1
    def css_resources(context, *args, **kwargs):
        return mark_safe(u'<link rel="stylesheet" href="%s/app_hook/styles.css">' % settings.STATIC_URL)


    # Example 2
    def user_about_info(context, *args, **kwargs):
        user = context['request'].user
        return format_html(
            "<b>{name}</b> {last_name}: {about}",
            name=user.first_name,
            last_name=user.last_name,
            about=mark_safe(user.profile.about_html_field)  # Some safe (sanitized) html data.
        )


    # Example 3
    def a_more_complex_hook(context, *args, **kwargs):
        # If you are doing this a lot, make sure to keep your templates in memory (google: django.template.loaders.cached.Loader)
        return render_to_string(
            template_name='templates/app_hook/head_resources.html',
            context_instance=context
        )


    # Example 4
    def an_even_more_complex_hook(context, *args, **kwargs):
        articles = Article.objects.all()
        return render_to_string(
            template_name='templates/app_hook/my_articles.html',
            dictionary={'articles': articles, },
            context_instance=context
        )

Registering a hook listener in a `third_party_app`:

    # third_party_app/apps.py

    from django.apps import AppConfig


    class MyAppConfig(AppConfig):

        name = 'myapp'
        verbose_name = 'My App'

        def ready(self):
            from hooks.templatehook import hook
            from third_party_app.template_hooks import css_resources

            hook.register("within_head", css_resources)

**Tip**

Where to register your hooks:

Use `AppConfig.ready()`:
[docs](https://docs.djangoproject.com/en/1.8/ref/applications/#django.apps.AppConfig.ready)
and
[example](http://chriskief.com/2014/02/28/django-1-7-signals-appconfig/)
