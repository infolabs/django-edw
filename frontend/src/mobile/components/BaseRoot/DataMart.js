import React, {useState, useMemo} from 'react'
import {View, Animated, ScrollView} from 'react-native'
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
import {dataMartStyles as styles} from "../../styles/dataMarts";


const {deviceHeight, deviceWidth} = platformSettings;
let translateY = deviceHeight;

const DataMart = props => {
  const {entry_point_id, entry_points, entities, terms} = props;
  const {viewComponents} = entities;
  const [animateTranslateY] = useState(new Animated.Value(translateY));
  const [visibleFilters, setVisibleFilters] = useState(false);

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

  const visibleFiltersBtn = terms.tree.json.length && (entities.items.objects.length || (terms.tagged.items
    && terms.tagged.items.length));

  return (
    <>
      <View style={styles.headerBtnView}>
        <View style={{...styles.headerBtn, ...styles.orderingView}}>
          <Ordering entry_points={entry_points} entry_point_id={entry_point_id}/>
        </View>
        <View style={{...styles.headerBtn, ...styles.viewAndFilteredIcon}}>
          {Object.keys(viewComponents.data).length > 1 ?
            <>
              <ViewComponentsBtn entry_points={entry_points} entry_point_id={entry_point_id}/>
              <View>
                <Text style={styles.textDelimiter}/>
              </View>
            </>
            : null
          }
          {visibleFiltersBtn  ?
            <FilterBtn entry_points={entry_points} entry_point_id={entry_point_id}
                       showFilters={() => showFilters(!visibleFilters)}/>
            : null
          }
        </View>
      </View>
      <Entities entry_points={entry_points} entry_point_id={entry_point_id}/>
      <Animated.View style={{...styles.termTreeAnimatedView, transform: [{translateY: animateTranslateY}]}}>
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
