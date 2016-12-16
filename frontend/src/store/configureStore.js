if (process.env.NODE_ENV === 'production') {
  module.exports = require('store/configureStore.prod');
} else {
  module.exports = require('store/configureStore.dev');
}
