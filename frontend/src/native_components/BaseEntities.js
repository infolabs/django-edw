import React, {useEffect} from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {View} from 'react-native';
import parseRequestParams from '../utils/parseRequestParams';
import ActionCreators from '../actions';
import Spinner from 'react-native-loading-spinner-overlay';
import Tile from './BaseEntities/Tile';
import List from './BaseEntities/List';
import {baseEntitiesStyles as styles} from '../native_styles/baseEntities';


const UNSUPPORTED_RES = [/.*ymap/];

export function filterUnsupported(components) {
  return components.filter(c => !UNSUPPORTED_RES.some(r => r.test(c)));
}


export function getTemplates() {
  return {
    tile: Tile,
    list: List,
  };
}


const defaultProps = {
  getTemplates,
};


function BaseEntities(props) {

  const {entities, entry_points, entry_point_id} = props;

  useEffect(() => {
    const request_params = entry_points[entry_point_id].request_params || [];

    const params = parseRequestParams(request_params),
      term_ids = params.term_ids,
      subj_ids = params.subj_ids,
      limit = params.limit,
      options_arr = params.options_arr;

    let request_options = entities.items.meta.request_options;

    if (limit > -1)
      request_options.limit = limit;

    if (term_ids.length)
      request_options.terms = term_ids;

    props.notifyLoadingEntities();
    props.readEntities(entry_point_id, subj_ids, request_options, options_arr);
  }, []);


  const items = entities.items.objects || [],
    {loading, meta} = entities.items,
    dataMart = meta.data_mart;

  const templateIsDataMart = !entry_points[entry_point_id].template_name ||
      (entry_points[entry_point_id].template_name === 'data-mart');

  if (dataMart) {
    const dmComponents = filterUnsupported(Object.keys(dataMart.view_components));
    const componentName = dmComponents.indexOf(meta.view_component) > -1 ? meta.view_component : dmComponents[0];

    const templates = props.getTemplates();
    const component = templates[componentName];
    const {notifyLoadingEntities, getEntities, fromRoute} = props;
    return (React.createElement(
      component, {
        items,
        meta,
        loading,
        entry_point_id,
        notifyLoadingEntities,
        getEntities,
        templateIsDataMart,
        fromRoute
      }
    ));
  } else if (templateIsDataMart) {
    return (
      <View style={styles.spinnerContainer}>
        <Spinner visible={true}/>
      </View>
    );
  } else {
    return null;
  }
}

BaseEntities.defaultProps = defaultProps;

const mapStateToProps = state => ({
  terms: state.terms,
  entities: state.entities,
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(BaseEntities);
