import React, {useState, useMemo} from 'react'
import {View, StyleSheet, Animated, ScrollView} from 'react-native'
import {Text, TopNavigation, Button, useTheme} from "@ui-kitten/components";
import {connect} from 'react-redux'
import Ordering from "../Ordering"
import FilterBtn from "../FilterBtn"
import Entities from "../Entities"
import ActionCreators from "../../actions"
import {bindActionCreators} from "redux"
import platformSettings from "../../constants/Platform";
import {Icon} from "native-base";
import TermsTree from "../TermsTree";
import getDeclinedName from "../../utils/getDeclinedName";
import ViewComponentsBtn from "../ViewComponentsBtn";


const {deviceHeight, deviceWidth} = platformSettings;
let translateY = deviceHeight;

const DataMart = props => {
  const {entry_point_id, entry_points, entities, terms} = props;
  const {data} = entities.viewComponents;
  const [animateTranslateY] = useState(new Animated.Value(translateY));
  const [visibleFilters, setVisibleFilters] = useState(false);

  const styles = StyleSheet.create({
    headerBtnView: {
      width: deviceWidth,
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 15,
    },
    headerBtn: {
      height: 50
    },
    orderingView: {
      width: '40%',
      marginRight: '30%',
    },
    textDelimiter: {
      width: 1,
      height: 18,
      backgroundColor: '#b4b4b4'
    },
    viewAndFilteredIcon: {
      width: 100,
      flexDirection: 'row',
      justifyContent: 'center',
      alignItems: 'center'
    },
    termTreeAnimatedView: {
      height: deviceHeight,
      width: deviceWidth,
      position: 'absolute',
      backgroundColor: '#fff',
      transform: [{translateY: animateTranslateY}],
      bottom: 0,
      zIndex: 4
    },
    termsTreeView: {
      height: '100%',
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
    },
    showObjectsBtnView: {
      position: 'absolute',
      bottom: 0,
      height: 120,
      width: deviceWidth,
      shadowOffset: {
        width: 0,
        height: 2
      },
      shadowOpacity: 0.4,
      shadowRadius: 10,
      borderTopWidth: 1,
      borderRadius: 15,
      borderColor: '#d5d5d5',
      backgroundColor: "#fff"
    },
    showObjectsBtn: {
      borderWidth: 0,
      marginHorizontal: 25,
      marginTop: 10,
      borderRadius: 10
    },
    emptyView: {
      height: 200
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
    translateY = visible ? 30 : deviceHeight;
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
      <View style={styles.headerBtnView}>
        <View style={{...styles.headerBtn, ...styles.orderingView}}>
          <Ordering entry_points={entry_points} entry_point_id={entry_point_id}/>
        </View>
        <View style={{...styles.headerBtn, ...styles.viewAndFilteredIcon}}>
          {Object.keys(data).length > 1 ?
            <>
              <View style={{}}>
                <ViewComponentsBtn entry_points={entry_points} entry_point_id={entry_point_id}/>
              </View>
              <View>
                <Text style={styles.textDelimiter}/>
              </View>
            </>
            : null
          }
          <View style={{}}>
            <FilterBtn entry_points={entry_points} entry_point_id={entry_point_id}
              showFilters={() => showFilters(!visibleFilters)}/>
          </View>
        </View>
      </View>
      <Entities entry_points={entry_points} entry_point_id={entry_point_id}/>
      <Animated.View style={styles.termTreeAnimatedView}>
        <TopNavigation
          alignment='center'
          title={() => <Text style={{...styles.termTreeViewTitle, backgroundColor: theme['background-color-default']}}>
            Фильтры
          </Text>}
          accessoryRight={renderBackAction}
        />
        <View style={styles.termsTreeView}>
          <ScrollView>
            <TermsTree entry_points={entry_points} entry_point_id={entry_point_id}/>
            {/*HACK: Чтобы добавить место в конце ScrollView нужно добавить пустой View*/}
            <View style={styles.emptyView}/>
          </ScrollView>
        </View>
        <View style={styles.showObjectsBtnView}>
          <Button
            style={{...styles.showObjectsBtn, backgroundColor: theme['color-primary-400']}}
            size="giant"
            onPress={() => showFilters(!visibleFilters)}>
            {`Показать ${getDeclinedName(entities.items.meta.count)}`}
          </Button>
        </View>
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
