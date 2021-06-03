import React, {useState, useRef, useEffect, useMemo} from 'react';
import {View, Animated, ScrollView} from 'react-native';
import {Text, TopNavigation, Button, useTheme} from '@ui-kitten/components';
import {Icon} from 'native-base';
import {dataMartStyles as styles} from '../../styles/dataMarts';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import getDeclinedName from '../../utils/getDeclinedName';
import ActionCreators from '../../actions';
import platformSettings from 'constants/Platform';
import {isArraysEqual} from 'utils/isArrayEqual';
import TermsTree from '../TermsTree';
import Ordering from '../Ordering';
import FilterBtn from '../FilterBtn';
import ViewComponentsBtn from '../ViewComponentsBtn';
import Entities, {getTemplatesDetail} from 'components_native/Entities';


const { deviceHeight } = platformSettings;


function DataMart(props) {
  const {entry_point_id, entry_points, entities, terms} = props;
  const {viewComponents, detail} = entities;
  const {data} = detail;
  const visibleFiltersBtn = entities.items.objects.length
    || (terms.tagged.items && terms.tagged.items.length && !entities.loading);

  const [visibleFilters, setVisibleFilters] = useState(false);
  const [showTermsTree, setShowTermsTree] = useState(false);
  const [templateDetailName, setTemplateDetailName] = useState(null);
  const [templatesDetail, setTemplatesDetail] = useState(null);

  const templates = useMemo(() => getTemplatesDetail(), []);

  const theme = useTheme();

  const refs = useRef({
    termsIdsTaggedBranch: new Set(),
    usePrevTerms: false,
    translateY: deviceHeight,
  });

  const animateTranslateY = useRef(new Animated.Value(0));

  useEffect(() => {
    Animated.timing(animateTranslateY.current, {
      toValue: refs.current.translateY,
      duration: 300,
      useNativeDriver: true,
    }).start();
  }, [refs.current.translateY, animateTranslateY]);

  useEffect(() => {
    const model = data.entity_model in templates ? data.entity_model : 'default';
    setTemplatesDetail(templates);
    setTemplateDetailName(model);
  }, [data, templates]);

  function visibilityFilters(visible) {
    if (refs.current.usePrevTerms) {
      const termsItems = terms.tagged.prevItems;
      props.notifyLoadingTerms();
      props.loadTree(entry_point_id, termsItems);
    } else
      setShowTermsTree(true);
    setVisibleFilters(visible);
    refs.current.translateY = visible ? 30 : deviceHeight;
    refs.current.usePrevTerms = false;
  }

  function closeFilters() {
    visibilityFilters(false);
    const {items, prevItems} = terms.tagged;
    if (!isArraysEqual(items, prevItems)) {
      const meta = entities.items.meta;
      const {subj_ids} = meta;
      props.notifyLoadingEntities();
      props.getEntities(entry_point_id, subj_ids, {}, [], true);
      refs.current.usePrevTerms = true;
    }
    setShowTermsTree(false);
  }

  function closeFiltersView() {
    return <Icon onPress={() => closeFilters()} name={'close'} />;
  }

  return (
    <>
      <View style={styles.headerBtnView}>
        <View style={{...styles.headerBtn, ...styles.orderingView}}>
          <Ordering entities={entities} entry_points={entry_points} entry_point_id={entry_point_id}/>
        </View>
        <View style={{...styles.headerBtn, ...styles.viewAndFilteredIcon}}>
          {Object.keys(viewComponents.data).length > 1 ?
            <>
              <ViewComponentsBtn entities={entities}/>
              <View>
                <Text style={styles.textDelimiter}/>
              </View>
            </>
            : null
          }
          {visibleFiltersBtn ?
            <FilterBtn entry_points={entry_points} entry_point_id={entry_point_id}
                       termsIdsTaggedBranch={refs.current.termsIdsTaggedBranch}
                       visibilityFilters={() => visibilityFilters(!visibleFilters)}/>
            : null
          }
        </View>
      </View>
      <Entities entry_points={entry_points} entry_point_id={entry_point_id}/>
      <Animated.View style={{...styles.termTreeAnimatedView, transform: [{translateY: animateTranslateY.current}]}}>
        {showTermsTree ?
          <>
            <TopNavigation
              alignment={'center'}
              title={() => <Text
                style={{...styles.navigationTitle, backgroundColor: theme['background-color-default']}}>
                Фильтры
              </Text>}
              accessoryRight={closeFiltersView}
            />
            <View style={styles.termsTreeView}>
              <ScrollView>
                <TermsTree entry_points={entry_points} entry_point_id={entry_point_id}
                           termsIdsTaggedBranch={refs.current.termsIdsTaggedBranch}/>
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
            hideVisibleDetail: props.hideVisibleDetail,
          })
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
