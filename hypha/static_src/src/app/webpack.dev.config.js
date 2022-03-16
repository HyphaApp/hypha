var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var ExtraWatchWebpackPlugin = require("extra-watch-webpack-plugin");

var config = require('./webpack.base.config')
devConfig = config("development")

// override django's STATIC_URL for webpack bundles
devConfig.output.publicPath = 'http://localhost:3000/app/'

// Add HotModuleReplacementPlugin and BundleTracker plugins
devConfig.plugins = devConfig.plugins.concat([
    new webpack.HotModuleReplacementPlugin(),
    new webpack.NoEmitOnErrorsPlugin(),
    new BundleTracker({filename: './hypha/static_compiled/app/webpack-stats.json'}),
    new webpack.EnvironmentPlugin({
        API_BASE_URL: 'http://apply.localhost:8000/api',
    }),
    new ExtraWatchWebpackPlugin({
        dirs: ['./hypha/static_src/src/javascript/'],
    }),
])

// Add a loader for JSX files with react-hot enabled

devConfig.devServer = {
    headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*',
    },
    host: 'localhost',
    port: 3000,
    allowedHosts: ['all'],
    client: {
        overlay: true,
    }
}

devConfig.devtool = 'source-map'

module.exports = devConfig
