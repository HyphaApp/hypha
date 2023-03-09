Hypha consists of three distinctive components:

1. First is the **Apply Site**, where people seeking for funds can apply by submitting their applications, the submission goes through different stages before it being approved for funding. After the applications are approved, they can be converted to a project. Apply site allows to manage the lifecycle of a project starting from a PAF to contracting to invoicing.

2. Then the **Admin or Wagtail Admin**, is used to create custom forms, setup funds/labs and workflow around them. Think of it as the back-office of for your submissions and projects.

3. Hypha also provides capability to build landing pages and display available funds and labs through **public site**.


```
                            Integrations                           
                            ┌────────────┐ ┌────────────┐          
                            │   Email    │ │   Slack    │          
                            └────────────┘ └────────────┘          
                            ┌────────────┐ ┌────────────┐          
                            │ Amazon S3  │ │   Sentry   │          
                            └────────────┘ └────────────┘          
                                                                    
                                                                    

    ┌────────────┐
    │PUBLIC SITE │◀────┐                            Databases
    └────────────┘     │      ┌────────────┐        ┌ ─ ─ ─ ─ ─ ─ ─ ─
    ┌────────────┐     │      │  Django /  │          ┌────────────┐ │
    │ APPLY SITE │◀────┼──────│  Wagtail   │◀───────│ │ PostgreSQL │
    └────────────┘     │      └────────────┘          └────────────┘ │
    ┌────────────┐     │                            │
    │  WAGTAIL   │     │                             ─ ─ ─ ─ ─ ─ ─ ─ ┘
    │   ADMIN    │◀────┘
    └────────────┘
```

## Public site

!!! warning Public Site is depreciated and will be removed
    The public is due for removal. Read more at https://github.com/HyphaApp/hypha/pull/3110

The Public site is intended to be a heavily cached public site with no behaviour that requires authentication, excluding the Wagtail Admin. The ultimate aim would be to serve this site statically.

The coupling between the Public and Apply sites has been done in such as way as to minimise the interaction between the two sites and facilitate a means of separation should the need arise. Their relationship is defined in the Public fund models:

## Apply site

@TODO

## Wagtail Admin

@TODO


## Django

Hypha is built on top of the Django Web Framework. All the pages are rendered server side. It uses wagtail CMS for creating and managing custom application forms, public pages and settings.

### Wagtail

Wagtail is used in Hypha to construct and manage forms, pages, users and user roles via an admin interface (and code). In other words, Hypha uses Wagtail to build pages (using `blocks`), modify view-level behavior (using `hooks`), and create an admin interface for customizing settings like user permissions.

**Hooks**: modifying the view-level behavior. Used in Hypha for copied round pages

**Blocks**: components used to build the views and input fields for webpages. Wagtail blocks are used to construct the main `streamfield` block to be inherited by Pages (`StoryBlock`) — composed of: `ImageBlock`, `DocumentBlock`, `QuoteBlock`, `BoxBlock`, `MoreBlock`, `ApplyLinkBlock`

### Media

Media is encouraged to be split into two distinct storage locations. A Public and a Private location, applicant media should exist only in the Private location. This is for two reasons:

1. This separates the site media, which is served publicly with no authentication, from the Applicant media, which has permissions checks, it reduces the risk of a miss-configured storage exposing the Applicant data.
2. Maintains separation between the two halves of the platform, Apply and Public.

Media should also be served from a view that inherits from the [PrivateMediaView](https://github.com/HyphaApp/hypha/blob/main/hypha/apply/utils/storage.py) which will confirm that the file isn't made public and can be configured to return the file object from an authenticated view.

### URL configuration

The two site have different url configurations, this limits the Apply site to a subset of the urls in the project. This is configured as part of the middleware stack using [apply\_url\_conf\_middleware](https://github.com/HyphaApp/hypha/blob/main/hypha/apply/middleware.py). This swaps out the url configuration based on the site homepage configured in the wagtail admin.

The default url configuration is for the Public site which are shared by the Public and Apply sites.

The Public site has access to the "public authentication" urls, this enables reverse lookup of the url in templates, such as the [login button](https://github.com/HyphaApp/hypha/blob/main/hypha/public/utils/templates/utils/includes/login_button.html), but the user is redirected to the apply site. Visiting [https:///login](https:///login) will present a login screen.


## External Integrations

### Sentry

Hypha uses sentry to monitor and track errors in Django. You can either self host or use their SaaS offering.

### Slack

If configured, Hypha is able to send out notifications to different slack channels for activities happening on the Hypha application related to submissions and projects.

### Email

Emails in Hypha are used for password recovery and sending out important notifications to the users.
