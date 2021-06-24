import React from 'react'
import {View} from 'react-native'
import ActionCreators from "../actions"
import {connect} from 'react-redux'
import {bindActionCreators} from "redux"
import {Text, Button, useTheme} from "@ui-kitten/components"
import {Icon} from "native-base";
import {filtersStyles as styles} from "../native_styles/filters";


const FilterBtn = props => {
  const {entities, visibilityFilters, termsIdsTaggedBranch} = props;
  const theme = useTheme();

  return (
    <Button onPress={() => visibilityFilters()} size='tiny' appearance='ghost' status='basic'>
      <View style={styles.filteredView}>
        <Icon name='funnel-outline' style={{fontSize: theme['icon-size']}}/>
        {termsIdsTaggedBranch.size ?
          <View style={{...styles.filteredBadge, backgroundColor: theme['color-primary-500']}}>
            <Text style={styles.filteredBadgeText}>{termsIdsTaggedBranch.size}</Text>
          </View>
          : null
        }
      </View>
    </Button>
  )
};

const mapStateToProps = state => ({
  entities: state.entities
});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(FilterBtn);
