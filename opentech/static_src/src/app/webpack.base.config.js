var path = require('path');

var COMMON_ENTRY = ['@babel/polyfill', './src/datetime']

module.exports = {
    context: __dirname,

    entry: {
        submissionsByRound: COMMON_ENTRY.concat(['./src/submissionsByRoundIndex']),
        submissionsByStatus: COMMON_ENTRY.concat(['./src/submissionsByStatusIndex']),
    },
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
            '@middleware': path.resolve(__dirname, 'src/redux/middleware'),
            '@api': path.resolve(__dirname, 'src/api'),
        }
    }
};
