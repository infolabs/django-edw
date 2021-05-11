import React, {useState, useEffect, useMemo} from 'react'
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
import {isArraysEqual} from "../../utils/isArrayEqual";


const {deviceHeight, deviceWidth} = platformSettings;
let translateY = deviceHeight;
let usePrevTerms = false;

const DataMart = props => {
  const {entry_point_id, entry_points, entities, terms} = props;
  const {viewComponents} = entities;
  const {termsIdsStructureIsLimb, loading, json} = terms.tree;
  const [animateTranslateY] = useState(new Animated.Value(translateY));
  const [visibleFilters, setVisibleFilters] = useState(false);
  // Флаг нужен для того, чтобы не показывать термины, пока не отсеяться ненужные.
  // Т.к. при первоначальной загрузке мы получаем абсолютно все термины
  const [showTermsTree, setShowTermsTree] = useState(false);

  useEffect(() => {
    let countTaggedBranch = 0;
    terms.tagged.items.map(item => {
      if (termsIdsStructureIsLimb.includes(item))
        countTaggedBranch++;
    });
    props.setCountTaggedBranch(countTaggedBranch);
    if(json.length)
      setShowTermsTree(true);
  },[terms.tagged.items]);

  useMemo(() => {
    Animated.timing(animateTranslateY, {
      toValue: translateY,
      duration: 300,
      useNativeDriver: true
    }).start();
  }, [translateY]);

  const visibilityFilters = visible => {
    if (usePrevTerms) {
      const termsItems = terms.tagged.prevItems;
      props.notifyLoading();
      props.loadTree(entry_point_id, termsItems);
    } else
      setShowTermsTree(true);
    setVisibleFilters(visible);
    translateY = visible ? 30 : deviceHeight;
    usePrevTerms = false;
  };

  const theme = useTheme();

  const closeFilters = () => {
    visibilityFilters(false);
    const {items, prevItems} = terms.tagged;
    if (!isArraysEqual(items, prevItems)) {
      const meta = entities.items.meta;
      const {subj_ids} = meta;
      props.notifyLoadingEntities();
      props.getEntities(entry_point_id, subj_ids, {}, [], true);
      usePrevTerms = true;
    }
    setShowTermsTree(false)
  };

  // HACK. Свойство onPress у TopNavigationAction не работает. Поэтому пришлось использовать иконку с native-base
  const closeFiltersView = () => (
    <Icon onPress={() => closeFilters()} name='close'/>
  );

  if (entities.items.meta.count === 0 && terms.tagged.entities_ignore) {
    return (
      <View style={styles.emptyContainerEntities}>
        <Text style={styles.emptyContainerEntitiesText}>Нет объектов</Text>
      </View>
    );
  }

  const visibleFiltersBtn = entities.items.objects.length || (terms.tagged.items
    && terms.tagged.items.length && !entities.loading);

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
          {visibleFiltersBtn ?
            <FilterBtn entry_points={entry_points} entry_point_id={entry_point_id}
                       visibilityFilters={() => visibilityFilters(!visibleFilters)}/>
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
          accessoryRight={closeFiltersView}
        />
        <View style={styles.termsTreeView}>
          {showTermsTree ?
            <ScrollView>
              <TermsTree entry_points={entry_points} entry_point_id={entry_point_id}/>
              {/*HACK: Чтобы добавить место в конце ScrollView нужно добавить пустой View*/}
              <View style={styles.emptyView}/>
            </ScrollView>
            : null
          }
        </View>
        {entities.items.meta.count !== undefined ?
          <View style={styles.showObjectsBtnView}>
            <Button
              style={{...styles.showObjectsBtn, backgroundColor: theme['color-primary-400']}}
              size="giant"
              onPress={() => visibilityFilters(!visibleFilters)}>
              {`Показать ${getDeclinedName(entities.items.meta.count)}`}
            </Button>
          </View>
          : null
        }
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
