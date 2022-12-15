# Implementation Details

## Media

Media is encouraged to be split into two distinct storage locations. A Public and a Private location, applicant media should exist only in the Private location. This is for two reasons:

1. This separates the site media, which is served publicly with no authentication, from the Applicant media, which has permissions checks, it reduces the risk of a miss-configured storage exposing the Applicant data.
2. Maintains separation between the two halves of the platform, Apply and Public.

Media should also be served from a view that inherits from the [PrivateMediaView](https://github.com/HyphaApp/hypha/blob/main/hypha/apply/utils/storage.py) which will confirm that the file isn't made public and can be configured to return the file object from an authenticated view.

## Public site

### Security

The Public site is intended to be a heavily cached public site with no behaviour that requires authentication, excluding the Wagtail Admin. The ultimate aim would be to serve this site statically.

### Coupling

The coupling between the Public and Apply sites has been done in such as way as to minimise the interaction between the two sites and facilitate a means of separation should the need arise. Their relationship is defined in the Public fund models:

* [BaseApplicationPage.application\_type](https://github.com/HyphaApp/hypha/blob/main/hypha/public/funds/models.py)
* [LabPage.lab\_type](https://github.com/HyphaApp/hypha/blob/main/hypha/public/funds/models.py)

#### Data: Public to Apply

The public site relies on the apply site to provide information on the related round status, open or closed and any closing dates for the round. The majority of this is within the [apply cta](https://github.com/HyphaApp/hypha/blob/main/hypha/public/funds/templates/public_funds/includes/fund_apply_cta.html).

Removing the database relationship and exposing the required data over an API would be all thats required to split the two sites.

#### Data: Apply to Public

The `application_public` and `lab_public` relations are then exposed on the application models through the `detail` attribute which is used to provide a link back to the public page in a few locations. References to these attributes should be kept to a minimum and could be replaced with a URL field to achieve seperation of Public and Apply portions of the project.

## URL configuration

The two site have different url configurations, this limits the Apply site to a subset of the urls in the project. This is configured as part of the middleware stack using [apply\_url\_conf\_middleware](https://github.com/HyphaApp/hypha/blob/main/hypha/apply/middleware.py). This swaps out the url configuration based on the site homepage configured in the wagtail admin.

The default url configuration is for the Public site which are shared by the Public and Apply sites.

The Public site has access to the "public authentication" urls, this enables reverse lookup of the url in templates, such as the [login button](https://github.com/HyphaApp/hypha/blob/main/hypha/public/utils/templates/utils/includes/login_button.html), but the user is redirected to the apply site. Visiting [https:///login](https:///login) will present a login screen.

