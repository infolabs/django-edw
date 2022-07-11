import React from 'react';
import {View} from 'react-native'
import ActionCreators from '../actions';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {useTheme, Button} from '@ui-kitten/components';
import Icon from 'react-native-vector-icons/Ionicons';
import {filterUnsupported} from './BaseEntities';


function ViewComponentsBtn(props) {
  const {meta} = props.entities.items;
  const {data_mart, request_options, subj_ids, view_component } = meta;
  const dataKeys = filterUnsupported(Object.keys(data_mart.view_components));
  let index = dataKeys.indexOf(view_component);
  index = index > -1 ? index : 0;
  const nextKey = dataKeys[index + 1] || dataKeys[0];
  const theme = useTheme();

  function changeViewComponent() {
    const options = Object.assign(request_options, {view_component: nextKey, offset: 0});
    const params = {
      mart_id: data_mart.id,
      options_obj: options,
      subj_ids,
    };

    props.notifyLoadingEntities();
    props.getEntities(params);
  }

  let iconName = null;

  if (nextKey.match(/(_list$)/))
    iconName = 'list-outline';
  else if (nextKey.match(/(_tile$)/))
    iconName = 'grid-outline';
  else if (nextKey.match(/(_map$)/))
    iconName = 'map-outline';

  return (
    <Button onPress={changeViewComponent} size="tiny" appearance="ghost" status="basic">
      <View>
        <Icon name={iconName} style={{fontSize: theme['icon-size']}}/>
      </View>
    </Button>
  );
}


const mapStateToProps = state => ({
  entities: state.entities,
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);


export default connect(mapStateToProps, mapDispatchToProps)(ViewComponentsBtn);
