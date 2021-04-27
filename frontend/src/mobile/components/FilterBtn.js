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
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 5,
    justifyContent: 'center'
  },
  filteredText: {
    fontSize: 16,
    marginRight: 10
  },
  filteredBadge: {
    width: 15,
    height: 15,
    backgroundColor: 'blue',
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute',
    top: -2,
    right: -5
  },
  filteredBadgeText: {
    fontSize: 12,
    color: '#fff'
  }
});

const FilterBtn = props => {
  const {entities, entry_points, entry_point_id, showFilters} = props;
  const theme = useTheme();

  return (
    <Button onPress={() => showFilters()} size='tiny' appearance='ghost' status='basic'>
      <View style={styles.filteredView}>
        <Text style={{...styles.filteredText, color: theme['color-default']}}>Фильтры</Text>
        <View>
          <Icon name='filter-outline'/>
          <View style={{...styles.filteredBadge, backgroundColor: theme['color-primary-500']}}>
            <Text style={styles.filteredBadgeText}>1</Text>
          </View>
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
