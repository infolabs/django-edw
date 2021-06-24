import React, {useState, useEffect, useMemo} from 'react'
import {View, Animated, ScrollView, Platform} from 'react-native'
import {Text, TopNavigation, Button, useTheme} from "@ui-kitten/components";
import {connect} from 'react-redux'
import Ordering from "../Ordering"
import FilterBtn from "../FilterBtn"
import Entities from "native_components/Entities";
import ActionCreators from "../../actions"
import {bindActionCreators} from "redux"
import platformSettings from "../../constants/Platform";
import {Icon} from "native-base";
import TermsTree from "../TermsTree";
import getDeclinedName from "../../utils/getDeclinedName";
import ViewComponentsBtn from "../ViewComponentsBtn";
import {dataMartStyles as styles} from "../../native_styles/dataMarts";
import {isArraysEqual} from "../../utils/isArrayEqual";


const {deviceHeight, deviceWidth} = platformSettings;
const termsIdsTaggedBranch = new Set();
let translateY = deviceHeight;
let usePrevTerms = false;

const DataMart = props => {
  const {entry_point_id, entry_points, entities, terms} = props;
  const {viewComponents, detail} = entities;
  const {loading, json} = terms.tree;
  const {data} = detail;
  const [animateTranslateY] = useState(new Animated.Value(translateY));
  const [visibleFilters, setVisibleFilters] = useState(false);
  const [visibleDetail, setVisibleDetail] = useState(false);
  // Флаг showTermsTree нужен для того, чтобы не показывать термины, пока не отсеяться ненужные.
  // Т.к. при первоначальной загрузке мы получаем абсолютно все термины
  const [showTermsTree, setShowTermsTree] = useState(false);
  const [templateDetailName, setTemplateDetailName] = useState(null);
  const [templatesDetail, setTemplatesDetail] = useState(null);

  useEffect(() => {
    if (!json.length)
      termsIdsTaggedBranch.clear();
  }, []);

  useEffect(() => {
    if (json.length)
      setShowTermsTree(true);
  }, [terms.tagged.items]);

  useEffect(() => {
    const templates = Entities.getTemplatesDetail();
    const model = data.entity_model in templates ? data.entity_model : "default";
    setTemplatesDetail(templates);
    setTemplateDetailName(model);
  }, [detail.data]);

  useEffect(() => {
    if (detail.visible) {
      if (Platform.OS === 'android'){
        translateY = 0
      } else {
        if (deviceHeight < 700) {
          translateY = 0;
        } else {
          translateY = 35;
        }
      }
      setShowTermsTree(false);
      setVisibleDetail(true);
    } else {
      translateY = deviceHeight;
      setVisibleDetail(false);
    }
  }, [detail.visible]);

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
      props.notifyLoadingTerms();
      props.loadTree(entry_point_id, termsItems);
    } else
      setShowTermsTree(true);
    setVisibleFilters(visible);
    if (visible) {
      if (Platform.OS === 'android'){
        translateY = 0;
      } else {
        if (deviceHeight < 700) {
          translateY = 0;
        } else {
          translateY = 35;
        }
      }
    } else {
      translateY = deviceHeight;
    }
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
                       termsIdsTaggedBranch={termsIdsTaggedBranch}
                       visibilityFilters={() => visibilityFilters(!visibleFilters)}/>
            : null
          }
        </View>
      </View>
      <Entities entry_points={entry_points} entry_point_id={entry_point_id}/>
      <Animated.View style={{...styles.termTreeAnimatedView, transform: [{translateY: animateTranslateY}]}}>
        {showTermsTree ?
          <>
            <TopNavigation
              alignment='center'
              style={{marginTop: 20}}
              title={() => <Text
                style={{...styles.navigationTitle, backgroundColor: theme['background-color-default']}}>
                Фильтры
              </Text>}
              accessoryRight={closeFiltersView}
            />
            <View style={styles.termsTreeView}>
              <ScrollView>
                <TermsTree entry_points={entry_points} entry_point_id={entry_point_id}
                           termsIdsTaggedBranch={termsIdsTaggedBranch}/>
                {/*HACK: Чтобы добавить место в конце ScrollView добавляем пустой View*/}
                <View style={styles.emptyView}/>
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
          </>
          : null
        }
        {detail.visible ?
          React.createElement(templatesDetail[templateDetailName],{
            data,
            hideVisibleDetail: props.hideVisibleDetail
          })
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
