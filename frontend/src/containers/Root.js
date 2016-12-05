import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import TermsTree from '../components/TermsTree';
import Entities from '../components/Entities';

export default class Root extends Component {

  render() {
    const { store, dom_attrs } = this.props;

    return (
      <Provider store={store}>
        <div className="row">
          <div className="col-sm-4 col-md-3 sidebar-filter">
            <TermsTree dom_attrs={dom_attrs} />
          </div>
          <div className="col-sm-8 col-md-9">
            <Entities dom_attrs={dom_attrs} />
          </div>
        </div>
      </Provider>
    );
  }
}

