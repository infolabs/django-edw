import React from 'react'
import {View} from 'react-native'
import ActionCreators from "../actions"
import {connect} from 'react-redux'
import {bindActionCreators} from "redux"
import {Text, Button, useTheme} from "@ui-kitten/components"
import {Icon} from "native-base";
import {filtersStyles as styles} from "../styles/filters";


const FilterBtn = props => {
  const {entities, entry_points, entry_point_id, visibilityFilters, terms} = props;
  const {countTaggedBranch} = terms;
  const theme = useTheme();

  return (
    <Button onPress={() => visibilityFilters()} size='tiny' appearance='ghost' status='basic'>
      <View style={styles.filteredView}>
        <Icon name='funnel-outline' style={{fontSize: theme['icon-size']}}/>
        {countTaggedBranch ?
          <View style={{...styles.filteredBadge, backgroundColor: theme['color-primary-500']}}>
            <Text style={styles.filteredBadgeText}>{countTaggedBranch}</Text>
          </View>
          : null
        }
      </View>
    </Button>
  )
};

const mapStateToProps = state => ({
  entities: state.entities,
  terms: state.terms
});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(FilterBtn);
