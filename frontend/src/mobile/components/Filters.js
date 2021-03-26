import React from 'react'
import {bindActionCreators} from "redux";
import ActionCreators from "../actions";
import {connect} from "react-redux";
import {Text, TopNavigation, useTheme} from "@ui-kitten/components";
import {SafeAreaView} from "react-native-safe-area-context";
import {Icon} from "native-base";
import {StyleSheet} from "react-native";
import platformSettings from "../constants/Platform";
import TermsTree from './TermsTree';


const {deviceHeight, deviceWidth} = platformSettings;

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  navigation: {
    fontSize: 18,
    fontWeight: 'bold',
    paddingHorizontal: 40,
    textAlign: 'center'
  },
  scrollView: {
    paddingTop: 10,
  },
  layout: {
    flex: 1,
    alignItems: 'center',
    width: deviceWidth,
    paddingHorizontal: 16,
  }
});

const Filters = props => {
  const {navigation} = props,
        {entry_point_id, entry_points, terms} = props.route.params;

  const theme = useTheme();

  // HACK. Свойство onPress у TopNavigationAction не работает. Поэтому пришлось использовать иконку с native-base
  const renderBackAction = () => (
    <Icon onPress={navigation.goBack} name='close'/>
  );

  return(
    <SafeAreaView style={{...styles.safeArea, backgroundColor: theme['background-color-default']}}>
      <TopNavigation
        alignment='center'
        title={() => <Text style={{...styles.navigation, backgroundColor: theme['background-color-default']}}>
          Фильтры</Text>}
        accessoryLeft={renderBackAction}
      />
      {/*TODO: Не работает. В компонент не прокидываются state.terms*/}
      {/*<TermsTree entry_points={entry_points} entry_point_id={entry_point_id}/>*/}
    </SafeAreaView>
  )
};

const mapStateToProps = state => ({});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(Filters);
