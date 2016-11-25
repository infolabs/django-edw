import React, { Component } from 'react';
import { Provider } from 'react-redux';
import TermsTree from '../components/TermsTree';
import Entities from '../components/Entities';

export default class Root extends Component {
  render() {
    const { store } = this.props;
    return (
      <Provider store={store}>
        <div className="terms-tree-container">
          <TermsTree />
          <Entities />
        </div>
      </Provider>
    );
  }
}

