import React, { Component } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Actions from '../../actions/index'
import Entities from 'components/Entities';
import Filters from 'components/Filters';
import Paginator from 'components/Paginator';
import ViewComponents from 'components/ViewComponents';
import Ordering from 'components/Ordering';
import Limits from 'components/Limits';
import Statistics from 'components/Statistics';
import Aggregation from 'components/Aggregation';
import DataMartsList from 'components/DataMartsList';
import GroupTitle from 'components/GroupTitle';
import {closest} from "../../utils/querySelector";


export class DataMart extends Component {

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

    const { entry_point_id, entry_points, actions, entities, terms } = this.props;

    if (!entities.loading && !entities.items.loading && !entities.items.objects.length && terms.tree &&
      terms.tree.json && terms.tree.json.length) {
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
      <div className="row ex-datamart">
        {
          Object.keys(entry_points).length > 1 &&
            <div className="ex-datamart__col ex-datamart__datamarts">
              <DataMartsList
                entry_points={entry_points}
                entry_point_id={entry_point_id}
                actions={actions}
              />
            </div>
        }
        <div className="ex-datamart__col ex-datamart__col--small sidebar-filter">
          <Filters entry_points={entry_points} entry_point_id={entry_point_id}/>
        </div>
        <div className="ex-datamart__col ex-datamart__col--big main-col">
          <div className="main-col__top maincol-top">
            <div className="maincol-top__col ex-view-as">
              <ViewComponents entry_points={entry_points} entry_point_id={entry_point_id} />
            </div>
            <div className="maincol-top__col ex-order-by ex-dropdown ex-state-closed">
              <Ordering entry_points={entry_points} entry_point_id={entry_point_id} />
            </div>
            <div className="maincol-top__col ex-howmany-items ex-dropdown ex-state-closed">
              <Limits entry_points={entry_points} entry_point_id={entry_point_id} />
            </div>
            <div className="maincol-top__col ex-statistic">
              <Statistics entry_points={entry_points} entry_point_id={entry_point_id} />
            </div>
          </div>
          <div className="row">
            <div className="ex-datamart__col ex-group-title">
              <GroupTitle/>
            </div>
          </div>
          <Entities entry_points={entry_points} entry_point_id={entry_point_id} />
          <Paginator entry_points={entry_points} entry_point_id={entry_point_id} />
          <Aggregation entry_points={entry_points} entry_point_id={entry_point_id} />
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


export default connect(mapState, mapDispatch)(DataMart);
