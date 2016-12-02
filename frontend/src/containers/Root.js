import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import TermsTree from '../components/TermsTree';
import Entities from '../components/Entities';

export default class Root extends Component {

  render() {
    const { store, mart_id } = this.props;

    return (
      <Provider store={store}>
        <div className="row">
          <div className="col-sm-4 col-md-3 sidebar-filter">
            <TermsTree mart_id={mart_id} />
          </div>
          <div className="col-sm-8 col-md-9">
            <Entities mart_id={mart_id} />
          </div>
        </div>
      </Provider>
    );
  }
}

