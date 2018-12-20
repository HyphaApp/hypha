var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')

var config = require('./base.config.js')

// Use webpack dev server
// config.entry = [
    // 'webpack-dev-server/client?http://localhost:3000',
    // 'webpack/hot/only-dev-server',
    // './assets/js/index'
// ]

// override django's STATIC_URL for webpack bundles
config.output.publicPath = 'http://localhost:3000/assets/bundles/'

// Add HotModuleReplacementPlugin and BundleTracker plugins
config.plugins = config.plugins.concat([
    new webpack.HotModuleReplacementPlugin(),
    new webpack.NoEmitOnErrorsPlugin(),
    new BundleTracker({filename: './webpack-stats.json'}),
])

// Add a loader for JSX files with react-hot enabled

config.devServer = {
    hot: true
}

config.mode = "development"

module.exports = config
