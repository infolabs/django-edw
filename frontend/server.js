const webpackDevServer = require('webpack-dev-server');
const webpack = require('webpack');

const config = require('./webpack.config');
const options = {
  publicPath: config.output.publicPath,
  hot: true,
  watchOptions: { poll: true },
  historyApiFallback: true,
  disableHostCheck: true,
  sockPort: 3000,
  headers: {
      "Access-Control-Allow-Origin": "*",
      'Access-Control-Allow-Credentials': true,
  },
  stats: {
    colors: true
  }
};

webpackDevServer.addDevServerEntrypoints(config, options);
const compiler = webpack(config);
const server = new webpackDevServer(compiler, options);

server.listen(3000, '0.0.0.0', err => {
  if (err)
    console.error(err);

  console.log('dev server listening on port 3000');
});
