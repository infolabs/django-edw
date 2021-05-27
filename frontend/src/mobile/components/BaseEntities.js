import React, {useEffect, useMemo} from 'react';
import {useSelector, useDispatch, useStore} from 'react-redux';
import {View} from 'react-native';
import Tile from './BaseEntities/Tile';
import List from './BaseEntities/List';
import parseRequestParams from '../utils/parseRequestParams';
import {
  notifyLoadingEntities,
  readEntities,
  setCurrentView,
  getEntities,
  getEntity,
  setDataViewComponents,
} from '../actions/EntityActions';
import ParticularInitiativeTile from './Entities/ParticularInitiativeTile';
import ParticularInitiativeList from './Entities/ParticularInitiativeList';
import ParticularProblemTile from './Entities/ParticularProblemTile';
import ParticularProblemList from './Entities/ParticularProblemList';
import Spinner from 'react-native-loading-spinner-overlay';
import Default from './Detail/Default';
import Problem from './Detail/Problem';
import Idea from './Detail/Idea';
import {baseEntitiesStyles as styles} from '../styles/baseEntities';


function getTemplates() {
  return {
    'tile': Tile,
    'list': List,
    'particular_initiative_tile': ParticularInitiativeTile,
    'particular_initiative_list': ParticularInitiativeList,
    'particular_problem_tile': ParticularProblemTile,
    'particular_problem_list': ParticularProblemList,
  };
}


export function getTemplatesDetail() {
  return {
    'default': Default,
    'particularproblem': Problem,
    'particularinitiative': Idea,
  };
}


function BaseEntities(props) {

  const {entry_points, entry_point_id} = props;

  const entities = useSelector(state => state.entities);
  const dispatch = useDispatch();
  const store = useStore();

  const templates = useMemo(() => getTemplates(), []);

  const params = useMemo(
    () => {
      const request_params = entry_points[entry_point_id].request_params || [];
      return parseRequestParams(request_params);
    },
    [entry_points, entry_point_id],
  );


  useMemo(
    () => {
      const meta = entities.items.meta;

      if (entities.viewComponents.currentView
          || !meta.data_mart
          || !meta.data_mart.view_components)
        return;

      let viewComponents = Object.keys(meta.data_mart.view_components);

      // Вычисляем список ключей компонентов, которые пересекаются c API и getTemplates
      let viewComponentsMobile = [];
      let templateIsRelated = entry_points[entry_point_id].template_name &&
        entry_points[entry_point_id].template_name === 'related';

      for (let item of viewComponents) {
        if (templateIsRelated && item.match(/(_list$)/) && templates.hasOwnProperty(item)) {
              viewComponentsMobile.push(item);
          continue;
        }
        if (templates.hasOwnProperty(item))
          viewComponentsMobile.push(item);
      }

      if (templateIsRelated && !viewComponentsMobile.length)
        viewComponentsMobile.push('list');

      const dataViewComponent = {};
      viewComponentsMobile.map(component => {
        dataViewComponent[component] = meta.data_mart.view_components[component];
      });

      setDataViewComponents(dataViewComponent);

      if (viewComponentsMobile.length) {
        const componentName = viewComponentsMobile[0];
        setCurrentView(componentName)(dispatch);
      }
    },
    [entities, templates, entry_points, entry_point_id, dispatch]
  );

  useEffect(() => {
    const term_ids = params.term_ids,
      subj_ids = params.subj_ids,
      limit = params.limit,
      options_arr = params.options_arr;

    let request_options = {};

    if (limit > -1)
      request_options.limit = limit;

    if (term_ids.length)
      request_options.terms = term_ids;

    notifyLoadingEntities()(dispatch);
    readEntities(entry_point_id,
      subj_ids, request_options, options_arr)(dispatch, store.getState);

  }, [params, entry_point_id, dispatch, store]);


  const items = entities.items.objects || [],
    {loading, meta} = entities.items,
    loadingEntity = entities.detail.loading;

  const templateIsDataMart = !entry_points[entry_point_id].template_name ||
      (entry_points[entry_point_id].template_name === 'data-mart');

  const componentName = entities.viewComponents.currentView || null;
  if (componentName) {
    const component = templates[componentName] || templates.list;
    return (React.createElement(
      component, {
        items,
        meta,
        loading,
        loadingEntity,
        entry_point_id,
        notifyLoadingEntities,
        getEntities,
        templateIsDataMart,
        getEntity,
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


export default BaseEntities;
