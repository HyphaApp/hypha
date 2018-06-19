
# Simple tooling

This is a lighter version of the [DIBB](https://github.com/torchbox/design-in-browser-bootstrap), using the same tooling but without Pattern Lab.

## What's required

It is assumed the developer's computer is running OSX or Linux. Depending on your setup you may already have the below installed;

* [Node.js](http://nodejs.org) (version 4.x.x)
* Optional: [Yarn](https://yarnpkg.com/en/docs/install)

## What's included

* [SASS](http://sass-lang.com/) CSS with [auto-prefixing](https://github.com/postcss/autoprefixer).
* [Browsersync](https://www.browsersync.io) for autoreloading.
* [Rollup](https://rollupjs.org) and [Babel](https://babeljs.io) for ES2015 support with module loading.
* Rollup plugins (`rollup.config.js`):
  * eslint
  * uglifyjs with sourcemaps (disabled by default)
  * support for using any installed node modules on the webiste
  * display file size information
* Consideration for images, currently copying the directory only - to avoid slowdowns and non-essential dependancies. We encourage using SVG for UI vectors and pre-optimised UI photograph assets.
* [Build commands](#build-scripts) for generating testable or deployable assets only

## Installation

To start a prototype using this bootstrap;

* **Get the files:** Clone this repository to a new directory, for example
`git clone https://github.com/SimonDEvans/simple-tooling.git new-project`.
* **Name the project:** Open `package.json` and replace the `name` with your project name [following npm guidelines](http://browsenpm.org/package.json#name).
* **Setup git**: Run `npm run git:init` in the root of your new project to remove existing git links with this repository and create a fresh project with the directory as is committed.
* **Install dependencies** Run `yarn install` to run the install process. `npm install` will work too, see [section about yarn below](#using-yarn).


## Developing with it

* To start the development environment, run `yarn start`, or alternatively `npm start` - to stop this process press `ctrl + c`.
* This will start Browsersync and make the project available at `http://localhost:3000/html/`. If another process is using this port, check terminal for an updated URL. You can change this configuation by modifying the `browsersync.config.js` file, documented here https://www.browsersync.io/docs/options.
* Source files for developing your project are in `src` and the distribution folder for the compiled assets is `dist`. Any changes made to files in the `dist` directory will be overwritten.

### Using yarn

* Yarn is the recommended way to install and upgrade node modules. It's like npm but [handles dependencies better](http://stackoverflow.com/questions/40057469/what-is-the-difference-between-yarn-lock-and-npm-shrinkwrap#answer-40057535).
* Install yarn itself: https://yarnpkg.com/en/docs/install
* Install all packages from `package.json`: `yarn install`
* Add new packages with yarn: `yarn add --dev package_name` (this will add it to `package.json` and `yarn.lock` too)
* Upgrade packages: `yarn upgrade-interactive`
* Keep using `npm` for running npm scripts. Although `yarn run` seems to work as well but `npm-run-all` might not use yarn, so stick to `npm run` for now.


## Deploying it

### Build scripts

To only build assets for either development or production you can use

 * `npm run build` To build development assets
 * `npm run build:prod` To build assets with minification and vendor prefixes

### Debug script

To test production, minified and vendor prefixed assets you can use

 * `npm run debug` To develop with a simple http server, no browsersync and production assets

## License

Copyright (c) 2017 Torchbox Ltd

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
