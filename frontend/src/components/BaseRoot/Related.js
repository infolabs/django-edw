import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import Actions from '../../actions/index'
import Paginator from 'components/Paginator';
import Entities from 'components/Entities';
import DataMartsList from 'components/DataMartsList'


class Related extends Component {

  render() {

    const { entities, entry_points, entry_point_id, actions } = this.props;

    const count = entities.meta.count;

    let el_with_count = ['ex-data-mart', 'ex-data-mart-container'];

    for(const item of el_with_count) {
      const elements = document.getElementsByClassName(item);
      //for (const element of elements) {
      for (let i = elements.length - 1; i >= 0; i--) {
        const element = elements[i],
            pk = element.attributes.getNamedItem('data-selected-entry-point-id') &&
                element.attributes.getNamedItem('data-selected-entry-point-id').value;
        if (pk && pk == entry_point_id) {
          element.setAttribute("data-data-count", count);
        }
      }
    }

    let mart_url = entry_points[entry_point_id].url || "",
        mart_name = entry_points[entry_point_id].name || "";

    const multi = Object.keys(entry_points).length > 1;

    const title = (
      <div className="col-md-9 ex-title">
        { mart_url != '' ? (
          <h3><a href={mart_url} title={mart_name}>{mart_name}</a></h3>
          ) : (
          <h3>{mart_name}</h3>
        )}
      </div>
    );

    return (
      <div className="ex-related-datamart">
        <div className="row">
          {
            multi ? <div className="col-md-9"> <DataMartsList
              entry_points={entry_points}
              entry_point_id={entry_point_id}
              actions={actions}
            /> </div> : title
          }
          <div className="col-md-3 ex-paginator">
            <Paginator entry_points={entry_points}
                       entry_point_id={entry_point_id}
                       hide_page_numbers={true}/>
          </div>
        </div>
        <div>
          <Entities entry_points={entry_points}
                    entry_point_id={entry_point_id} />
        </div>
      </div>
    );
  }
}

function mapState(state) {
  return {
    entities: state.entities.items,
  };
}

function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
    dispatch: dispatch
  };
}


export default connect(mapState, mapDispatch)(Related);
