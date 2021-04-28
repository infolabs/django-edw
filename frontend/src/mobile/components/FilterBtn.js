import React from 'react'
import {View, StyleSheet} from 'react-native'
import ActionCreators from "../actions"
import {connect} from 'react-redux'
import {bindActionCreators} from "redux"
import {Text, Button, useTheme} from "@ui-kitten/components"
import {Icon} from "native-base";
import platformSettings from "../constants/Platform";


const {deviceHeight, deviceWidth} = platformSettings;

const styles = StyleSheet.create({
  filteredView: {
    paddingTop: 3
  },
  filteredBadge: {
    width: 12,
    height: 12,
    backgroundColor: 'blue',
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute',
    top: 0,
    right: -3
  },
  filteredBadgeText: {
    fontSize: 9,
    color: '#fff'
  }
});

const FilterBtn = props => {
  const {entities, entry_points, entry_point_id, showFilters} = props;
  const theme = useTheme();

  return (
    <Button onPress={() => showFilters()} size='tiny' appearance='ghost' status='basic'>
      <View style={styles.filteredView}>
        <Icon name='funnel-outline' style={{fontSize: theme['icon-size']}}/>
        <View style={{...styles.filteredBadge, backgroundColor: theme['color-primary-500']}}>
          <Text style={styles.filteredBadgeText}>1</Text>
        </View>
      </View>
    </Button>
  )
};

const mapStateToProps = state => ({
  entities: state.entities
});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(FilterBtn);
