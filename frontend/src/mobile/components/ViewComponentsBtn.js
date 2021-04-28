import React from 'react'
import ActionCreators from "../actions"
import {connect} from 'react-redux'
import {bindActionCreators} from "redux"
import {useTheme, Button} from "@ui-kitten/components"
import {Icon} from "native-base";


const ViewComponentsBtn = props => {
  const {entities, entry_points, entry_point_id, showFilters} = props;
  const {viewComponents} = entities;
  const {data, currentView} = viewComponents;
  const dataKeys = Object.keys(data);
  const index = dataKeys.indexOf(currentView);
  const nextKey = dataKeys[index + 1] || dataKeys[0];
  const theme = useTheme();

  const changeViewComponent = () => {
    props.setCurrentView(nextKey)
  };

  let iconName = null;

  if (nextKey.match(/(_list$)/))
    iconName = 'list-outline';
  else if (nextKey.match(/(_tile$)/))
    iconName = 'grid-outline';
  else if (nextKey.match(/(_map$)/))
    iconName = 'map-outline';

  return (
    <Button onPress={() => changeViewComponent()} size='tiny' appearance='ghost' status='basic'>
      <Icon name={iconName} style={{fontSize: theme['icon-size']}}/>
    </Button>
  )
};

const mapStateToProps = state => ({
  entities: state.entities
});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(ViewComponentsBtn);
