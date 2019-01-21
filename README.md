opentech.fund Wagtail site
==================

## Contributing

1. Make changes on a new branch, including a broad category and the ticket number if relevant e.g. `feature/123-extra-squiggles`, `fix/newsletter-signup`.
1. Push your branch to the remote.
1. Edit details as necessary.



If you need to preview work on `staging`, this can be merged and deployed manually without making a merge request. You can still make the merge request as above, but add a note to say that this is on `staging`, and not yet ready to be merged to `master`.

# Setting up a local build

This repository includes a Vagrantfile for running the project in a Debian VM.

To set up a new build:

``` bash
git clone git@github.com:OpenTechFund/opentech.fund.git
cd opentech.fund
vagrant up
vagrant ssh
```

Then within the SSH session:

``` bash
dj migrate
dj createcachetable
dj createsuperuser
djrun
```

This will make the site available on the host machine at: http://127.0.0.1:8000/

# Updating front-end files

Any changes to sass and js files need to be made within the `opentech/static_src` directory. They then need to be compiled with the  help of "gulp".

Start a vagrant SSH session and go to the project root directory.

``` bash
vagrant ssh
cd /vagrant
```

Here you can run a number of different "gulp" commands. The two most useful are likely:

``` bash
gulp watch
```

That will watch all fles for changes and build them with maps etc., perfect for development. (It will also run the "collecstatic" command, useful when running the site with a production server and not the built in dev server.)

If you are working on the React components then it may be worth just using one of the two following commands. They should do the same thing, but the npm command calls Webpack direct.

| WARNING: You cannot use Webpack watch and Hot Module Reload within vagrant, it must be run from your own installation of node. All other commands will work. |
| --- |

``` bash
gulp watch:app
# OR
npm run webpack-watch
```

To build the assets which get deployed, use the following. The deployment scripts will handle this, and the files do not need to be committed.

``` bash
gulp build
```

For more command see the `gulpfile.js` file.


# Running tests

Run all tests for the project with the following command within the SSH session:

``` bash
DJANGO_SETTINGS_MODULE=opentech.settings.test python manage.py test --keepdb
```
