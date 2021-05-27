var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')

var config = require('./webpack.base.config.js')

staticDevConfig = config('production')

staticDevConfig.output.path = require('path').resolve('./assets/dist')

staticDevConfig.plugins = staticDevConfig.plugins.concat([
    new BundleTracker({ filename: './hypha/static_compiled/app/webpack-stats.json' }),
    new webpack.EnvironmentPlugin({
        NODE_ENV: 'production',
        API_BASE_URL: null ,
    }),
])

staticDevConfig.optimization = {}


/**
 * A webpack config similar to production, but produces development-oriented webpack-stats file.
 * This makes it possible to use React application without Webpack Dev Server.
 */
module.exports = staticDevConfig
