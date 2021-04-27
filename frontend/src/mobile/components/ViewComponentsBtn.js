import React, {useState, useEffect} from 'react'
import {View, StyleSheet} from 'react-native'
import ActionCreators from "../actions"
import {connect} from 'react-redux'
import {bindActionCreators} from "redux"
import {Text, useTheme, Button} from "@ui-kitten/components"
import platformSettings from "../constants/Platform";


const {deviceHeight, deviceWidth} = platformSettings;

const styles = StyleSheet.create({
  viewComponents: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 5,
    padding: 10,
    justifyContent: 'center'
  },
  viewComponentsText: {
    fontSize: 16,
    marginRight: 10
  }
});

const ViewComponentsBtn = props => {
  const {entities, entry_points, entry_point_id, showFilters} = props;
  const {viewComponents} = entities;
  const {data, currentView} = viewComponents;
  const dataKeys = Object.keys(data);
  const index = dataKeys.indexOf(currentView);
  const nextKey = dataKeys[index + 1] || dataKeys[0];
  const theme = useTheme();

  let [nextViewTitle, setNextViewTitle] = useState(null);

  useEffect(() => {
    setNextViewTitle(data[nextKey])
  }, [currentView]);

  const changeViewComponent = () => {
    props.setCurrentView(nextKey)
  };

  return (
    <Button onPress={() => changeViewComponent()} size='tiny' appearance='ghost' status='basic'>
      <View style={styles.viewComponents}>
        <Text style={{...styles.viewComponentsText, color: theme['color-default']}}>{nextViewTitle}</Text>
      </View>
    </Button>
  )
};

const mapStateToProps = state => ({
  entities: state.entities
});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(ViewComponentsBtn);
