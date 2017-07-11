import React, { Component } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Actions from '../actions/index'


class Aggregation extends Component {
  render() {
    const aggregation = this.props.entities.items.meta.aggregation;

    let ret = <span></span>;
    if (aggregation && Object.keys(aggregation).length) {
      let aggr = {}
      for (let k of Object.keys(aggregation)) {
        if (aggregation[k].name != null && aggregation[k].value != null)
          aggr[k] = aggregation[k];
      }

      if (Object.keys(aggr).length) {
        ret = (
          <ul className="ex-aggregation-attrs">
            {Object.keys(aggr).map(
              (k, i) => <li key={i} data-slug={k}>
                <strong>{ aggregation[k].name }:</strong>&nbsp;
                { aggregation[k].value }
              </li>
            )}
          </ul>
        )
      }
    }
    return ret;
  }
}


function mapState(state) {
  return {
    entities: state.entities,
  };
}

function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
    dispatch: dispatch
  };
}

export default connect(mapState, mapDispatch)(Aggregation);
