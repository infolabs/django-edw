const path = require('path');

const BundleTracker = require('webpack-bundle-tracker');
const TerserPlugin = require('terser-webpack-plugin');


// Абсолютные пути считаются от каталога frontend через __dirname: зашитых
// путей деплоя в конфиге больше нет, он работает в любом каталоге репозитория.
const FRONTEND_DIR = __dirname;
const REPO_DIR = path.resolve(__dirname, '..');
const SRC_DIR = path.resolve(__dirname, 'src');
const OUTPUT_DIR = path.resolve(__dirname, '..', 'backend', 'edw', 'static', 'edw', 'js');
const PUBLIC_PATH = '/static/edw/js/';


module.exports = (env = {}, argv = {}) => {
  const mode = argv.mode || env.mode || 'production';
  const isProduction = mode === 'production';

  return {
    mode,

    context: FRONTEND_DIR,

    devtool: isProduction ? false : 'eval-cheap-module-source-map',

    // В production entry только само приложение: клиент dev-server и
    // hot-middleware в бандл не попадают.
    entry: {
      bundle: path.resolve(SRC_DIR, 'index.js'),
    },

    output: {
      path: OUTPUT_DIR,
      filename: '[name].js',
      publicPath: PUBLIC_PATH,
    },

    optimization: {
      minimize: isProduction,
      minimizer: [
        new TerserPlugin({
          parallel: true,
          extractComments: false,
          terserOptions: {
            ecma: 2018,
            compress: {
              passes: 2,
            },
            mangle: true,
            format: {
              comments: false,
            },
          },
        }),
      ],
    },

    plugins: [
      new BundleTracker({
        path: FRONTEND_DIR,
        filename: 'webpack-stats.json',
        publicPath: PUBLIC_PATH,
      }),
    ],

    resolve: {
      // Как и раньше: модули ищутся сначала в src (импорты 'components/Root',
      // 'constants/Entities'), затем в node_modules frontend и репозитория.
      modules: [
        SRC_DIR,
        path.resolve(FRONTEND_DIR, 'node_modules'),
        'node_modules',
      ],
      extensions: ['.js', '.jsx'],
    },

    module: {
      rules: [
        {
          test: /\.jsx?$/,
          include: SRC_DIR,
          use: [{
            loader: 'babel-loader',
            options: {
              presets: ['@babel/preset-env', '@babel/preset-react'],
              // optional chaining и nullish coalescing входят в preset-env.
              plugins: [
                '@babel/plugin-proposal-class-properties',
              ],
              babelrc: false,
              cacheDirectory: false,
            },
          }],
        },
        {
          // Стили подключаются обычным import './less/styles.less' в index.js:
          // inline-цепочка !style!raw!less! больше не нужна.
          test: /\.less$/,
          include: SRC_DIR,
          use: [
            'style-loader',
            {
              loader: 'less-loader',
              options: {
                lessOptions: {
                  // math: 'always' — семантика арифметики less 2/3, на которую
                  // рассчитаны исходники EDW.
                  math: 'always',
                  javascriptEnabled: false,
                },
              },
            },
          ],
        },
        {
          test: /\.css$/,
          include: SRC_DIR,
          use: ['style-loader', 'css-loader'],
        },
      ],
    },

    performance: {
      hints: false,
    },

    stats: 'minimal',
  };
};
