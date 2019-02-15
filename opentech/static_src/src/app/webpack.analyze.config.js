const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

var config = require('./webpack.prod.config.js')

config.plugins = config.plugins.concat([
    new BundleAnalyzerPlugin(),
])

module.exports = config
