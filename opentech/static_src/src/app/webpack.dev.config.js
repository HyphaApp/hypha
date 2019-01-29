var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')

var config = require('./webpack.base.config')

// override django's STATIC_URL for webpack bundles
config.output.publicPath = 'http://localhost:3000/app/'

// Add HotModuleReplacementPlugin and BundleTracker plugins
config.plugins = config.plugins.concat([
    new webpack.HotModuleReplacementPlugin(),
    new webpack.NoEmitOnErrorsPlugin(),
    new BundleTracker({filename: './opentech/static_compiled/app/webpack-stats.json'}),
    new webpack.EnvironmentPlugin({
        API_BASE_URL: 'http://apply.localhost:8000/',
    }),
])

// Add a loader for JSX files with react-hot enabled

config.devServer = {
    headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*',
    },
    hotOnly: true,
    host: 'localhost',
    port: 3000,
    overlay: true
}

config.devtool = 'source-map'

config.mode = "development"

module.exports = config
