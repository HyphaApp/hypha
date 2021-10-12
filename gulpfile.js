'use strict';

var importOnce = require('node-sass-import-once');

var options = {};

// #############################
// Edit these paths and options.
// #############################

// The root paths are used to construct all the other paths in this
// configuration. The "project" root path is where this gulpfile.js is located.
options.rootPath = {
  project     : __dirname + '/',
  app         : __dirname + '/hypha/',
  theme       : __dirname + '/hypha/static_src/'
};

options.theme = {
  root      : options.rootPath.theme,
  sass      : options.rootPath.theme + 'src/sass/',
  js        : options.rootPath.theme + 'src/javascript/',
  app       : options.rootPath.theme + 'src/app/',
  img       : options.rootPath.theme + 'src/images/',
  font      : options.rootPath.theme + 'src/fonts/',
  dest      : options.rootPath.app   + 'static_compiled/',
  css       : options.rootPath.app   + 'static_compiled/css/',
  js_dest   : options.rootPath.app   + 'static_compiled/js/',
  app_dest  : options.rootPath.app   + 'static_compiled/app/',
  img_dest  : options.rootPath.app   + 'static_compiled/images/',
  font_dest : options.rootPath.app   + 'static_compiled/fonts/'
};

// Define the node-sass configuration. The includePaths is critical!
options.sass = {
  importer: importOnce,
  includePaths: [
    options.theme.sass,
  ],
  outputStyle: 'expanded'
};

// Define the paths to the JS files to lint.
options.eslint = {
  files  : [
    options.theme.js + '**/*.js',
    '!' + options.theme.js + '**/*.min.js'
  ]
};

// If your files are on a network share, you may want to turn on polling for
// Gulp watch. Since polling is less efficient, we disable polling by default.
options.gulpWatchOptions = {interval: 600};
// options.gulpWatchOptions = {interval: 1000, mode: 'poll'};


// Load Gulp and tools we will use.
var gulp      = require('gulp'),
  del         = require('del'),
  sass        = require('gulp-dart-sass'),
  eslint      = require('gulp-eslint'),
  sassLint    = require('gulp-sass-lint'),
  sourcemaps  = require('gulp-sourcemaps'),
  size        = require('gulp-size'),
  babel       = require('gulp-babel'),
  uglify      = require('gulp-uglify'),
  cleanCSS    = require('gulp-clean-css'),
  touch       = require('gulp-touch-cmd'),
  webpack     = require('webpack'),
  webpackStrm = require('webpack-stream'),
  DevServer   = require('webpack-dev-server'),
  exec        = require('child_process').exec;


// Use Dart Sass instead of default node Sass.
sass.compiler = require('sass');

// Load webpack config
var webpackDev = () => require(options.theme.app + 'webpack.dev.config.js');
var webpackStaticDev = () => require(options.theme.app + 'webpack.static.dev.config.js');
var webpackProd = () => require(options.theme.app + 'webpack.prod.config.js');
var webpackAnalyze = () => require(options.theme.app + 'webpack.analyze.config.js');

// The sass files to process.
var sassFiles = [
  options.theme.sass + '**/*.scss',
  // Do not open Sass partials as they will be included as needed.
  '!' + options.theme.sass + '**/_*.scss'
];

// Clean CSS files.
gulp.task('clean:css', function clean () {
  return del([
      options.theme.css + '**/*.css',
      options.theme.css + '**/*.map'
    ], {force: true});
});

// Clean JavaScript files.
gulp.task('clean:js', function clean () {
  return del([
      options.theme.dest + 'app/*.*',
      options.theme.js_dest + '**/*.js',
      options.theme.js_dest + '**/*.map'
    ], {force: true});
});

// Clean all directories.
gulp.task('clean', gulp.parallel('clean:css', 'clean:js'));

// Lint JavaScript.
gulp.task('lint:js', function lint () {
  return gulp.src(options.eslint.files)
    .pipe(eslint())
    .pipe(eslint.format());
});

// Lint JavaScript and throw an error for a CI to catch.
gulp.task('lint:js-with-fail', function lint () {
  return gulp.src(options.eslint.files)
    .pipe(eslint())
    .pipe(eslint.format())
    .pipe(eslint.failOnError());
});

// Lint Sass.
gulp.task('lint:sass', function lint () {
  return gulp.src(options.theme.sass + '**/*.scss')
    .pipe(sassLint())
    .pipe(sassLint.format());
});

// Lint Sass and throw an error for a CI to catch.
gulp.task('lint:sass-with-fail', function lint () {
  return gulp.src(options.theme.sass + '**/*.scss')
    .pipe(sassLint())
    .pipe(sassLint.format())
    .pipe(sassLint.failOnError());
});

// Lint Sass and JavaScript.
gulp.task('lint', gulp.parallel('lint:sass', 'lint:js'));

// Build CSS.
gulp.task('styles', gulp.series('clean:css', function css () {
  return gulp.src(sassFiles)
    .pipe(sourcemaps.init())
    .pipe(sass(options.sass).on('error', sass.logError))
    .pipe(size({showFiles: true}))
    .pipe(sourcemaps.write('./'))
    .pipe(gulp.dest(options.theme.css))
    .pipe(touch());
}));

gulp.task('styles:production', gulp.series('clean:css', function css () {
  return gulp.src(sassFiles)
    .pipe(sass(options.sass).on('error', sass.logError))
    .pipe(cleanCSS({rebase: false}))
    .pipe(size({showFiles: true}))
    .pipe(gulp.dest(options.theme.css))
    .pipe(touch());
}));

// Build JavaScript.
gulp.task('scripts', gulp.series('clean:js', function js () {
  return gulp.src(options.theme.js + '**/*.js')
    .pipe(sourcemaps.init())
    .pipe(babel({presets: ['@babel/env']}))
    .pipe(size({showFiles: true}))
    .pipe(sourcemaps.write('./'))
    .pipe(gulp.dest(options.theme.js_dest));
}));

// Build JavaScript.
gulp.task('scripts:production', gulp.series('clean:js', function js () {
  return gulp.src(options.theme.js + '**/*.js')
    .pipe(babel({presets: ['@babel/env']}))
    .pipe(uglify())
    .pipe(size({showFiles: true}))
    .pipe(gulp.dest(options.theme.js_dest));
}));

// Build App.
gulp.task('app', function() {
    return gulp.src(options.theme.app + 'src/')
        .pipe(webpackStrm( webpackStaticDev() ))
        .pipe(gulp.dest(options.theme.app_dest));
})

// Build Prod App
gulp.task('app:production', function() {
    return gulp.src(options.theme.app + 'src/')
        .pipe(webpackStrm( webpackProd() ))
        .pipe(gulp.dest(options.theme.app_dest));
})

// Analyze Prod build of App
gulp.task('app:analyze', function() {
    return gulp.src(options.theme.app + 'src/')
        .pipe(webpackStrm( webpackAnalyze() ))
        .pipe(gulp.dest(options.theme.app_dest));
})


// Copy images.
gulp.task('images', function copy () {
  return gulp.src(options.theme.img + '**/*.*').pipe(gulp.dest(options.theme.img_dest));
});

// Copy fonts.
gulp.task('fonts', function copy () {
  return gulp.src(options.theme.font + '**/*.*').pipe(gulp.dest(options.theme.font_dest));
});

// Run Djangos collectstatic command.
gulp.task('collectstatic', function (collect) {
  exec('python manage.py collectstatic --no-post-process --noinput --verbosity 0', function (err, stdout, stderr) {
    collect(err);
    // console.log(stdout);
    // console.log(stderr);
  });
});

// Watch for changes and rebuild.
gulp.task('watch:css', gulp.series('styles', function watch () {
  return gulp.watch(options.theme.sass + '**/*.scss', options.gulpWatchOptions, gulp.series('styles'));
}));

gulp.task('watch:lint:sass', gulp.series('lint:sass', function watch () {
  return gulp.watch(options.theme.sass + '**/*.scss', options.gulpWatchOptions, gulp.series('lint:sass'));
}));

gulp.task('watch:lint:js', gulp.series('lint:js', function watch () {
  return gulp.watch(options.eslint.files, options.gulpWatchOptions, gulp.series('lint:js'));
}));

gulp.task('watch:js', gulp.series('scripts', function watch () {
  return gulp.watch(options.eslint.files, options.gulpWatchOptions, gulp.series('scripts'));
}));

gulp.task('watch:images', gulp.series('images', function watch () {
  return gulp.watch(options.theme.img + '**/*.*', options.gulpWatchOptions, gulp.series('images'));
}));

gulp.task('watch:fonts', gulp.series('fonts', function watch () {
  return gulp.watch(options.theme.font + '**/*.*', options.gulpWatchOptions, gulp.series('fonts'));
}));

gulp.task('watch:static', function watch () {
  return gulp.watch(options.theme.dest + '**/*.*', options.gulpWatchOptions, gulp.series('collectstatic'));
});

gulp.task('watch:app', function watch (callback) {
    var webpackOptions = webpackDev();

    webpackOptions.entry = Object.keys(webpackOptions.entry).reduce((acc, key) => {
        acc[key] = [
            `webpack-dev-server/client?http://localhost:${webpackOptions.devServer.port}/`,
            'webpack/hot/dev-server',
        ].concat(webpackOptions.entry[key])
        return acc;
    }, {});

    var serverOptions = Object.assign(
        {}, webpackOptions.devServer, {
            publicPath: '/app/',
            stats: {
                colors: true,
                cached: false,
                cachedAssets: false
            }
        }
    );

    var server = new DevServer(
        webpack( webpackOptions ),
        serverOptions
    )

    server.listen(3000, "localhost", function(err) {
        if(err) throw new console.PluginError("webpack-dev-server", err);
        // Server listening
        console.log("[webpack-dev-server]", "Running");
    });
})

gulp.task('watch', gulp.parallel('watch:css', 'watch:lint:sass', 'watch:js', 'watch:lint:js', 'watch:images', 'watch:fonts', 'watch:static'));

// Build everything.
gulp.task('build', gulp.series(gulp.parallel(gulp.series('styles:production', 'scripts:production', 'app:production'), 'images', 'fonts', 'lint'), 'collectstatic'));

// Deploy everything.
gulp.task('deploy', gulp.parallel(gulp.series('styles:production', 'scripts:production', 'app:production'), 'images', 'fonts'));

// The default task.
gulp.task('default', gulp.series('build'));
