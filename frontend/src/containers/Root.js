import React, { Component } from 'react';
import { Provider } from 'react-redux';
import TermsTree from '../components/TermsTree';
import Entities from '../components/Entities';

export default class Root extends Component {
  render() {
    const { store } = this.props;
    return (
      <Provider store={store}>
        <div className="row">
          <div className="col-sm-4 col-md-3 sidebar-filter">
            <TermsTree />
          </div>
          <div className="col-sm-8 col-md-9">
            <Entities />
          </div>
        </div>
      </Provider>
    );
  }
}

