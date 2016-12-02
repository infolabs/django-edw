import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import TermsTree from '../components/TermsTree';
import Entities from '../components/Entities';

export default class Root extends Component {

  componentDidMount() {
    const el = ReactDOM.findDOMNode(this);
    this.mart_id = el.parentNode.getAttribute("data-data-mart-id");
  }

  render() {
    const { store } = this.props;
    return (
      <Provider store={store}>
        <div className="row">
          <div className="col-sm-4 col-md-3 sidebar-filter">
            <TermsTree mart_id={this.mart_id} />
          </div>
          <div className="col-sm-8 col-md-9">
            <Entities mart_id={this.mart_id} />
          </div>
        </div>
      </Provider>
    );
  }
}

