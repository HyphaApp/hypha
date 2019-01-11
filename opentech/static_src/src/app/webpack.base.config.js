var path = require('path');

module.exports = {
    context: __dirname,

    entry: ['./src/index'],

    output: {
        filename: '[name]-[hash].js'
    },

    plugins: [
    ], // add all common plugins here

    module: {
        rules: [
            {
                test: /\.jsx?$/,
                loader: 'babel-loader',
                include: [path.resolve(__dirname, './src')],
                query: {
                    presets: ['@babel/preset-react', '@babel/preset-env'],
                    plugins: [
                        'react-hot-loader/babel',
                        '@babel/plugin-proposal-class-properties'
                    ]
                }
            },
            {
                test: /\.scss$/,
                use: [{
                    loader: 'style-loader'
                }, {
                    loader: 'css-loader',
                    options: {
                        sourceMap: true
                    }
                }, {
                    loader: 'sass-loader',
                    options: {
                        sourceMap: true,
                        data: '@import "main.scss";',
                        includePaths: [
                            path.join(__dirname, 'src')
                        ]
                    }
                }]
            },
            {
                test: /\.svg$/,
                use: ['@svgr/webpack']
            }
        ]
    },

    resolve: {
        modules: ['node_modules', './src'],
        extensions: ['.js', '.jsx']
    }
};
