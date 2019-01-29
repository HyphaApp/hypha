var path = require('path');

module.exports = {
    context: __dirname,

    entry: ['@babel/polyfill', './src/index'],

    output: {
        filename: '[name]-[hash].js'
    },

    plugins: [],

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
                },
            },
            {
                test: /\.js$/,
                exclude: /node_modules/,
                include: [path.resolve(__dirname, './src')],
                loader: 'eslint-loader',
                options: {
                    configFile: path.resolve(__dirname, './.eslintrc'),
                },
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
        extensions: ['.js', '.jsx'],
        alias: {
            '@components': path.resolve(__dirname, 'src/components'),
            '@containers': path.resolve(__dirname, 'src/containers'),
            '@redux': path.resolve(__dirname, 'src/redux'),
            '@reducers': path.resolve(__dirname, 'src/redux/reducers'),
            '@selectors': path.resolve(__dirname, 'src/redux/selectors'),
            '@actions': path.resolve(__dirname, 'src/redux/actions'),
            '@api': path.resolve(__dirname, 'src/api'),
        }
    }
};
