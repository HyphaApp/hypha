var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')

module.exports = {
    context: __dirname,

    entry: '../src/',

    output: {
        path: path.resolve('./assets/bundles/'),
        filename: "[name]-[hash].js"
    },

    plugins: [
    ], // add all common plugins here

    module: {
        rules: [
            {
                test: /\.jsx?$/,
                loader: 'babel-loader',
                include: [path.resolve(__dirname, '../src')],
                query: {
                    presets: ['@babel/preset-react']
                }
            }
        ]
    },

    resolve: {
        modules: ['node_modules'],
        extensions: ['.js', '.jsx']
    },
}
