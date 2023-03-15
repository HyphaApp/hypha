# Setting up error & performance monitoring

Hypha supports error tracking using https://sentry.io and comes pre-installed with `sentry-sdk`. Once enabled, you will be able to log unhandled exceptions and manually logged errors.

## Error Tracking

#### Python Error Tracking

To enable Sentry to track python and Django Errors, set `SENTRY_DSN` environment variable.

```shell
SENTRY_DSN="https://...."
```

#### Javascript Error Tracking

Add your sentry public key to `SENTRY_PUBLIC_KEY` environment variable. This will
add lazy-loaded sdk from Sentry CDN to all the templates, and then initialize it.

```shell
SENTRY_PUBLIC_KEY="2214b...."
```

You can set a comma separated `SENTRY_DENY_URLS` environment variable to exclude any page from being tracked. 

See more: https://docs.sentry.io/platforms/javascript/

## Performance monitoring

Set `SENTRY_TRACES_SAMPLE_RATE` to a value greater than `0` upto `1` to enable performance monitoring of both the Python and Javascript code. It requires that you
have already set `SENTRY_DSN` and/or `SENTRY_PUBLIC_KEY`.

```shell
SENTRY_TRACES_SAMPLE_RATE = "0.5"
```

## Sentry Environment

You can also set deployment environment using `SENTRY_ENVIRONMENT`. This string is freeform and set to `production` by default. A release can be associated with more than one environment to separate them in the UI (think staging vs production or similar)

```shell
SENTRY_ENVIRONMENT="staging"
```

## Debugging

If debug is enabled SDK will attempt to print out useful debugging information if something goes wrong with sending the event. The default is always false. It's generally not recommended to turn it on in production, though turning debug mode on will not cause any safety concerns.

```shell
SENTRY_DEBUG=true
```

## Advance Configuration

Make use of `/hypha/settings/local.py` and override `hypha/tempalates/base.html` to add custom initialization code. 

See https://docs.sentry.io/platforms/python/guides/django/configuration/ for more details.
