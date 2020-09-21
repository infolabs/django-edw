const path = require('path');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');

const app_name = 'django-edw';
const node_modules_path = `/app/${app_name}/node_modules/`;
const local_path = `/app/${app_name}/frontend/src/`;


module.exports = {
  context: '/app',
  devtool: 'eval',
  entry: [
    'whatwg-fetch',
    'webpack-dev-server/client?http://0.0.0.0:3000',
    'webpack/hot/only-dev-server',
    './src/index'
  ],
  output: {
    path: `/app/${app_name}/backend/edw/static/js/`,
    filename: "bundle.js",
  },
  plugins: [
    new BundleTracker({filename: './webpack-stats.json'})
  ],
  optimization: {
    minimizer: [new TerserPlugin({sourceMap: true})],
  },
  resolve: {
    modules: [
      path.resolve(local_path),
      path.resolve(node_modules_path)
    ],
    alias: {
      'react': path.join(node_modules_path, 'react'),
    },
    extensions: ['.js'],
  },
    module: {
    rules: [{
      test: /\.js$/,
      use: [{
          loader: 'babel-loader',
          options: {
            presets: ["@babel/preset-env", "@babel/preset-react"],
            plugins: [
              "@babel/plugin-proposal-class-properties",
              "@babel/plugin-proposal-function-bind",
            ],
            babelrc: false
          }
        },
      ],
      include: local_path
    }, {
      test: /\.css?$/,
      loaders: ['style-loader', 'raw-loader'],
      include: local_path
    }, {
      test: /\.less?$/,
      loaders: ["less-loader", "css-loader"],
      include: path.join(__dirname, 'less')
    }]
  }
};
