var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var config = require('./webpack.base.config.js')

prodConfig = config('production')

prodConfig.output.path = require('path').resolve('./hypha/static_compiled/app')

prodConfig.plugins = prodConfig.plugins.concat([
    new BundleTracker({filename: './hypha/static_compiled/app/webpack-stats-prod.json'}),
    new webpack.EnvironmentPlugin({
        NODE_ENV: 'production',
        API_BASE_URL: null ,
    }),
])

prodConfig.optimization = {}


module.exports = prodConfig
