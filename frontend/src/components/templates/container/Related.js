import React, { Component } from 'react';

export default class Related extends Component {
  render() {
    const { components,  dom_attrs, mart_id } = this.props,
          { TermsTree, Entities, Paginator,
            ViewComponents, Ordering, Limits, Statistics } = components;

    return (
      <div className="row">
        <Entities dom_attrs={dom_attrs} mart_id={mart_id} />
      </div>
    );
  }
}
