import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import Actions from '../../actions/index';
import Paginator from 'components/Paginator';
import Entities from 'components/Entities';
import DataMartsList from 'components/DataMartsList';
import Statistics from 'components/Statistics';
import { closest } from '../../utils/querySelector';


class Related extends Component {

  componentDidUpdate(prevProps) {
    // устанавливаем data-data-count и data-initial-data-count
    const prevCount = prevProps.entities.items && prevProps.entities.items.meta.count,
        { entities, entry_point_id } = this.props,
        count = entities.items.meta && entities.items.meta.count;
    if (count != prevCount || ((count === undefined) && (prevCount === undefined))) {
      const elements = document.getElementsByClassName('ex-data-mart');
      for (let i = elements.length - 1; i >= 0; i--) {
        const element = elements[i],
            pki = element.attributes.getNamedItem('data-selected-entry-point-id'),
            pk = pki && pki.value;
        if (pk == entry_point_id) {
          let targets = [element];
          const container = closest(element, '.ex-data-mart-container');
          if (container) {
            targets.push(container);
          }
          const is_initial = (prevCount === undefined) && (count !== undefined);
          for (let j = targets.length - 1; j >= 0; j--) {
            const target = targets[j];
            target.setAttribute("data-data-count", count);
            if (is_initial) {
              target.setAttribute("data-initial-data-count", count);
            } else if ((count === undefined) && (prevCount === undefined)) {
              target.setAttribute("data-initial-data-count", '0');
            }
          }
        }
      }
    }

  }

  render() {

    const { entry_points, entry_point_id, actions, entities, terms } = this.props;

    let entry_point = entry_points[entry_point_id],
        mart_url = entry_point.url || "",
        mart_name = entry_point.name || "";

    const multi = Object.keys(entry_points).length > 1;

    const title = (
      <div className="ex-title">
        { mart_url != '' ? (
          <h3><a href={mart_url} title={mart_name}>{mart_name}</a></h3>
          ) : (
          <h3>{mart_name}</h3>
        )}
      </div>
    );

    if (!entities.loading && !entities.items.loading && !entities.items.objects.length) {
      if (Object.keys(entry_points).length > 1 ) {
        return (
          <div className="row ex-datamart paddingtop20 paddingbottom20 d-flex flex-column">
            <DataMartsList
              entry_points={entry_points}
              entry_point_id={entry_point_id}
              actions={actions}
            />
            <span className="ex-empty">НET ОБЪЕКТОВ</span>
          </div>
        )
      } else {
        return (
          <div className="row ex-datamart paddingtop20 paddingbottom20">
            <span className="ex-empty">НET ОБЪЕКТОВ</span>
          </div>
        )
      }
    }

    return (
      <div className="ex-related-datamart">
        <div className="row">
          {
            multi ? <div className="ex-title"> <DataMartsList
              entry_points={entry_points}
              entry_point_id={entry_point_id}
              actions={actions}
            /> </div> : title
          }
          <div className="ex-statistic">
            <Statistics entry_points={entry_points} entry_point_id={entry_point_id} />
          </div>
          <div className="ex-paginator">
            <Paginator entry_points={entry_points}
                       entry_point_id={entry_point_id}
                       hide_page_numbers={true}/>
          </div>
        </div>
        <div className="ex-entities">
          <Entities entry_points={entry_points}
                    entry_point_id={entry_point_id} />
        </div>
      </div>
    );
  }
}

function mapState(state) {
  return {
    entities: state.entities,
    terms: state.terms
  };
}

function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
    dispatch: dispatch
  };
}


export default connect(mapState, mapDispatch)(Related);
