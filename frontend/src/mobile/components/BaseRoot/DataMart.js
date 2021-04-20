import React, {useState, useMemo} from 'react'
import {View, StyleSheet, Animated, ScrollView} from 'react-native'
import {Text, TopNavigation, useTheme} from "@ui-kitten/components";
import {connect} from 'react-redux'
import Ordering from "../Ordering"
import FilterBtn from "../FilterBtn"
import Entities from "../Entities"
import ActionCreators from "../../actions"
import {bindActionCreators} from "redux"
import platformSettings from "../../constants/Platform";
import {Icon} from "native-base";
import TermsTree from "../TermsTree";


const {deviceHeight, deviceWidth} = platformSettings;
let translateY = deviceHeight;

const DataMart = props => {
  const {entry_point_id, entry_points, entities, terms} = props;
  const [animateTranslateY] = useState(new Animated.Value(translateY));
  const [visibleFilters, setVisibleFilters] = useState(false);

  const styles = StyleSheet.create({
    sortAndFilteredView: {
      width: deviceWidth,
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 15,
    },
    termTreeView: {
      height: deviceHeight,
      width: deviceWidth,
      position: 'absolute',
      backgroundColor: '#fff',
      transform: [{translateY: animateTranslateY}],
      bottom: 0,
      zIndex: 4,
    },
    termTreeViewTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      paddingHorizontal: 40,
      textAlign: 'center'
    },
    emptyContainerEntities: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      marginTop: 10
    },
    emptyContainerEntitiesText: {
      fontSize: 18
    }
  });

  useMemo(() => {
    Animated.timing(animateTranslateY, {
      toValue: translateY,
      duration: 300,
      useNativeDriver: true
    }).start();
  }, [translateY]);

  const showFilters = visible => {
    setVisibleFilters(visible);
    translateY = visible ? 50 : deviceHeight;
  };

  const theme = useTheme();

  // HACK. Свойство onPress у TopNavigationAction не работает. Поэтому пришлось использовать иконку с native-base
  const renderBackAction = () => (
    <Icon onPress={() => showFilters(false)} name='close'/>
  );

  if (entities.items.meta.count === 0 && terms.tagged.entities_ignore) {
    return (
      <View style={styles.emptyContainerEntities}>
        <Text style={styles.emptyContainerEntitiesText}>Нет объектов</Text>
      </View>
    );
  }

  return (
    <>
      <View style={styles.sortAndFilteredView}>
        <Ordering entry_points={entry_points} entry_point_id={entry_point_id}/>
        <FilterBtn entry_points={entry_points} entry_point_id={entry_point_id}
                   showFilters={() => showFilters(!visibleFilters)}/>
      </View>
      <Entities entry_points={entry_points} entry_point_id={entry_point_id}/>
      <Animated.View style={styles.termTreeView}>
        <TopNavigation
          alignment='center'
          title={() => <Text style={{...styles.termTreeViewTitle, backgroundColor: theme['background-color-default']}}>
            Фильтры
          </Text>}
          accessoryRight={renderBackAction}
        />
        <TermsTree entry_points={entry_points} entry_point_id={entry_point_id}/>
      </Animated.View>
    </>
  )
};

const mapStateToProps = state => ({
  entities: state.entities,
  terms: state.terms
});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(DataMart);
