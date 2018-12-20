var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')

var config = require('./base.config.js')


// override django's STATIC_URL for webpack bundles
config.output.publicPath = 'http://localhost:3000/app/'

// Add HotModuleReplacementPlugin and BundleTracker plugins
config.plugins = config.plugins.concat([
    new webpack.HotModuleReplacementPlugin(),
    new webpack.NoEmitOnErrorsPlugin(),
    new BundleTracker({filename: './webpack-stats.json'}),
])

// Add a loader for JSX files with react-hot enabled

config.devServer = {
    contentBase: path.join(__dirname, '../../../../static_compiled/app'),
    disableHostCheck: true,
    hot: true,
    port: 3000,
    host: '0.0.0.0'
}

config.devtool = 'source-map'

config.mode = "development"

module.exports = config
