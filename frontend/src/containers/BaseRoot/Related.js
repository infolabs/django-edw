import React, { Component } from 'react';
import Entities from 'components/Entities';

export default class Related extends Component {
  render() {
    const { components,  dom_attrs, mart_id } = this.props;

    return (
      <div className="row">
        <Entities dom_attrs={dom_attrs} mart_id={mart_id} />
      </div>
    );
  }
}
