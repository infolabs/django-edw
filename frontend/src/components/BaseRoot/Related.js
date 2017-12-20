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

/*
    for(let item of el_with_count) {
      let elements = document.getElementsByClassName(item);
      for (let element of elements) {
        let pk = element.attributes.getNamedItem('data-data-mart-pk')
          ? element.attributes.getNamedItem('data-data-mart-pk').value : null;
        if (pk && pk == entry_point_id) {
          element.setAttribute("data-data-count", count);
        }
      }
    }
*/

    let mart_url = entry_points[entry_point_id].url || "",
        mart_name = entry_points[entry_point_id].name || "";

    let el_with_count = ['ex-data-mart', 'ex-data-mart-container'];
    return (
      <div className="ex-related-datamart">
        <div className="row">
          <div className="col-sm-12 col-md-12">
            {
              Object.keys(entry_points).length > 1 ? <DataMartsList
                entry_points={entry_points}
                entry_point_id={entry_point_id}
                actions={actions}
              /> : null
            }
          </div>
          <div className="col-md-9 ex-title">
            { mart_url != '' ? (
            <h3><a href={mart_url} title={mart_name}>{mart_name}</a></h3>
            ) : (
            <h3>{mart_name}</h3>
            )}
          </div>
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
