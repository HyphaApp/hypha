# Heroku

## DNS

Set up one address for the application environment.

Add the address first to Heroku to get the the DNS target for the CNAME entry.

!!! info
    If you are using Cloudflare ignore the DNS targets and use the Heroku application URL instead, something like `[dev-app-name].herokuapp.com`.

Add redirects for `robots.txt` and `favicon.ico` to `/static/robots.txt` and `/static/favicon.ico`.

## Heroku

Create a Heroku app for your project. A dev, test and live environment is good to have.

Connect the Heroku app to your git repo or push your code directly to Heroku. If you are using GitHub I recommend selecting it as the "deployment method".

Then so the following steps for each environment.

Set these settings as a minimum:

* `API_BASE_URL`
* `BASIC_AUTH_ENABLED`
* `BASIC_AUTH_LOGIN`
* `BASIC_AUTH_PASSWORD`
* `DJANGO_SETTINGS_MODULE`
* `EMAIL_HOST`
* `ON_HEROKU=true` (so correct production settings gets loaded)
* `ORG_LONG_NAME`
* `ORG_SHORT_NAME`
* `ORG_EMAIL`
* `SECRET_KEY` (see below for generating secret key)
* `SEND_MESSAGES`
* `SERVER_EMAIL`
* `STAFF_EMAIL_DOMAINS`

Generate secret key with:

```shell
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

1. Add Heroku Postgres as a add-on. "Hobby dev" or "Hobby basic" works for dev and test and "Standard 0" is a good start for production.
2. Add buildpacks for Nodejs and Python, make sure Nodejs is listed first.
3. Temporarily remove the "release" step from the "Procfile". It has a clear cache step that will fail until the cache tables are created.
4. Deploy the appropriate branch.
5. Activate dynos to run your app. For dev and test the "Hobby" level works well. For production a "Standard-2X" with a dyno count of 2 and WEB\_CONCURRENCY set to 3 performance well.
6. Run the following commands from the command line with the help of heroku-cli. If it's the first time you use heroku-cli you first need to login with `heroku login`:

    ```shell
    heroku run python3 manage.py migrate -a [name-of-app]
    heroku run python3 manage.py sync_roles -a [name-of-app]
    heroku run python3 manage.py createcachetable -a [name-of-app]
    heroku run python3 manage.py createsuperuser -a [name-of-app]
    heroku run python3 manage.py wagtailsiteupdate [the-public-address] [the-apply-address] 443  -a [name-of-app]
    ```

7. Now add the "release" step back to the `Procfile` and deploy again.

You should now have a running site.

## AWS S3

Set up a bucket for private files and another for public files. Private files are uploads on submissions.

Set these settings as a minimum:

* `AWS_ACCESS_KEY_ID`
* `AWS_SECRET_ACCESS_KEY`
* `AWS_STORAGE_BUCKET_NAME` (most often same as `AWS_PUBLIC_BUCKET_NAME`)
* `AWS_PRIVATE_BUCKET_NAME`
* `AWS_PUBLIC_BUCKET_NAME`

Optionally set these as well:

* `AWS_PUBLIC_CUSTOM_DOMAIN`
* `AWS_QUERYSTRING_EXPIRE`

### Private bucket

Properties:

Versioning enabled. Default encryption enables AES-256

CORS configuration:

```text
<?xml version="1.0" encoding="UTF-8"?>
<CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
<CORSRule>
    <AllowedOrigin>*</AllowedOrigin>
    <AllowedMethod>GET</AllowedMethod>
    <AllowedMethod>POST</AllowedMethod>
    <AllowedMethod>PUT</AllowedMethod>
    <MaxAgeSeconds>3000</MaxAgeSeconds>
    <AllowedHeader>*</AllowedHeader>
</CORSRule>
</CORSConfiguration>
```

### Public bucket

Properties:

Versioning enabled.

Access Control List:

Public access -&gt; Everyone -&gt; List Yes

CORS configuration:

```text
<?xml version="1.0" encoding="UTF-8"?>
<CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
<CORSRule>
    <AllowedOrigin>*</AllowedOrigin>
    <AllowedMethod>GET</AllowedMethod>
    <AllowedMethod>POST</AllowedMethod>
    <AllowedMethod>PUT</AllowedMethod>
    <MaxAgeSeconds>3000</MaxAgeSeconds>
    <AllowedHeader>*</AllowedHeader>
</CORSRule>
</CORSConfiguration>
```

Bucket policy:

```text
{
    "Version": "2012-10-17",
    "Id": "Policy1562302603386",
    "Statement": [
        {
            "Sid": "Stmt1562302600239",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::public.example.com/*"
        }
    ]
}
```

## Mailgun

Set:

* `MAILGUN_API_KEY`

And it should just work.

