var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')

var config = require('./webpack.base.config.js')

config.output.path = require('path').resolve('./assets/dist')

config.plugins = config.plugins.concat([
    new BundleTracker({filename: './opentech/static_compiled/app/webpack-stats-prod.json'}),
    new webpack.EnvironmentPlugin({
        NODE_ENV: 'production',
        API_BASE_URL: null ,
    }),
])

config.optimization = {
    minimize: true
}

config.mode = "production"

module.exports = config
