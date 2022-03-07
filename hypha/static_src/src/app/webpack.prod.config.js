var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var TerserPlugin = require("terser-webpack-plugin");
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

prodConfig.optimization = {
  minimize: true,
  minimizer: [new TerserPlugin({terserOptions: {
    compress: {
      drop_console: true,
    },
    mangle: true
  }})
],
}


module.exports = prodConfig
