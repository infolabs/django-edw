import React, {useState, useEffect, useMemo, useRef} from 'react';
import {View, Animated, ScrollView} from 'react-native';
import {Text, TopNavigation, Button, useTheme} from '@ui-kitten/components';
import {SafeAreaView} from 'react-native-safe-area-context';
import {connect} from 'react-redux';
import Ordering from '../Ordering';
import FilterBtn from '../FilterBtn';
import ActionCreators from '../../actions';
import {bindActionCreators} from 'redux';
import platformSettings from '../../constants/Platform';
import {Icon} from 'native-base';
import TermsTree from '../TermsTree';
import getDeclinedName from '../../utils/getDeclinedName';
import ViewComponentsBtn from '../ViewComponentsBtn';
import {filterUnsupported} from '../BaseEntities';
import {dataMartStyles as styles} from '../../native_styles/dataMarts';
import compareArrays from '../../utils/compareArrays';
import Entities from 'native_components/Entities';


const {deviceHeight} = platformSettings;

function DataMart(props) {
  const {entry_point_id, entry_points, entities, terms, fromRoute} = props;
  const termViewClasses = props.termViewClasses || [];
  const {json} = terms.tree;

  const refs = useRef({
    termsIdsTaggedBranch: new Set(),
    translateY: deviceHeight,
  }).current;

  const [animateTranslateY] = useState(new Animated.Value(refs.translateY));
  const [visibleFilters, setVisibleFilters] = useState(false);
  // Флаг showTermsTree нужен для того, чтобы не показывать термины, пока не отсеяться ненужные.
  // Т.к. при первоначальной загрузке мы получаем абсолютно все термины
  const [showTermsTree, setShowTermsTree] = useState(false);

  const theme = useTheme();

  useEffect(() => {
    if (!json.length)
      refs.termsIdsTaggedBranch.clear();
  }, []);

  useEffect(() => {
    if (json.length) {
      setShowTermsTree(true);
      const {prevItems} = terms.tagged;
      if (!prevItems.length)
        props.setPrevTaggedItems();
    }
  }, [terms.tagged.items]);

  useMemo(() => {
    Animated.timing(animateTranslateY, {
      toValue: refs.translateY,
      duration: 300,
      useNativeDriver: true,
    }).start();
  }, [refs.translateY]);


  function visibilityFilters(visible, usePrevTerms = false) {
    if (usePrevTerms) {
      const termsItems = terms.tagged.prevItems;
      props.notifyLoadingTerms();
      props.loadTree(entry_point_id, termsItems);
      refs.termsIdsTaggedBranch.clear();
    } else {
      setShowTermsTree(true);
    }
    setVisibleFilters(visible);
    if (visible)
      refs.translateY = 0;
    else
      refs.translateY = deviceHeight;
  }


  function closeFilters() {
    const {items, prevItems} = terms.tagged;
    if (!compareArrays(items, prevItems)) {
      const meta = entities.items.meta;
      const {subj_ids} = meta;
      props.notifyLoadingEntities();
      const params = {
        mart_id: entry_point_id,
        options_obj: {terms: prevItems},
        subj_ids,
      };
      props.getEntities(params);
      visibilityFilters(false, true);
    } else {
      visibilityFilters(false);
    }
    setShowTermsTree(false);
  }

  // HACK. Свойство onPress у TopNavigationAction не работает. Поэтому пришлось использовать иконку с native-base
  function closeFiltersView() {
    return <Icon onPress={closeFilters} name="close"/>;
  }

  if (entities.items.meta.count === 0 && terms.tagged.entities_ignore) {
    return (
      <View style={styles.emptyContainerEntities}>
        <Text style={styles.emptyContainerEntitiesText}>Нет объектов</Text>
      </View>
    );
  }

  const visibleFiltersBtn = entities.items.objects.length || (terms.tagged.items
    && terms.tagged.items.length && !entities.loading);

  const dataMart = entities.items.meta.data_mart;
  const viewComponents = dataMart ? filterUnsupported(Object.keys(dataMart.view_components)) : [];

  return (
    <>
      <View style={styles.headerBtnView}>
        <View style={{...styles.headerBtn, ...styles.orderingView}}>
          <Ordering entry_points={entry_points} entry_point_id={entry_point_id}/>
        </View>
        <View style={{...styles.headerBtn, ...styles.viewAndFilteredIcon}}>
          {viewComponents.length > 1 ?
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
                       termsIdsTaggedBranch={refs.termsIdsTaggedBranch}
                       visibilityFilters={() => visibilityFilters(!visibleFilters)}/>
            : null
          }
        </View>
      </View>
      <Entities entry_points={entry_points} entry_point_id={entry_point_id} fromRoute={fromRoute}/>
      <Animated.View style={{...styles.termTreeAnimatedView, transform: [{translateY: animateTranslateY}]}}>
        {showTermsTree ?
          <SafeAreaView>
            <TopNavigation
              alignment="center"
              title={() => <Text
                style={{...styles.navigationTitle, backgroundColor: theme['background-color-default']}}>
                Фильтры
              </Text>}
              accessoryRight={closeFiltersView}
            />
            <View style={styles.termsTreeView}>
              <ScrollView>
                <View style={styles.termsScrollViewContainer}>
                  <TermsTree entry_points={entry_points} entry_point_id={entry_point_id}
                             termsIdsTaggedBranch={refs.termsIdsTaggedBranch} termViewClasses={termViewClasses}/>
                </View>
              </ScrollView>
            </View>
            {entities.items.meta.count !== undefined ?
              <View style={styles.showObjectsBtnView}>
                <Button
                  style={{...styles.showObjectsBtn, backgroundColor: theme['color-primary-400']}}
                  size="giant"
                  onPress={() => {
                    visibilityFilters(!visibleFilters);
                    props.setPrevTaggedItems();
                  }}>
                  {`Показать ${getDeclinedName(entities.items.meta.count)}`}
                </Button>
              </View>
              : null
            }
          </SafeAreaView>
          : null
        }
      </Animated.View>
    </>
  );
}


const mapStateToProps = state => ({
  entities: state.entities,
  terms: state.terms,
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);


export default connect(mapStateToProps, mapDispatchToProps)(DataMart);
