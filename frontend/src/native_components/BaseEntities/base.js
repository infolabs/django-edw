import React, {useState, useRef, useEffect} from 'react';
import {useDispatch, useStore} from 'react-redux';
import {expandGroup, notifyLoadingEntities, getEntities} from '../../actions/EntitiesActions';
import {ScrollView, View, ImageBackground, StyleSheet} from 'react-native';
import Spinner from 'react-native-loading-spinner-overlay';
import {Badge} from 'native-base';
import {Text, Card, Layout, List} from '@ui-kitten/components';
import Singleton from '../../utils/singleton';


export const maxLengthDescriptionTile = 70;
export const maxLengthDescriptionListRelated = 90;
const mediaRegExp = /.*<img.*?src=(['"])(.*?)(['"])/;
const RELATED_CONTAINER_SIZE = {
  large: 'large'
};
const IGNORE_EXTRA_KEYS = [

]

export const stylesComponent = StyleSheet.create({
  badge: {
    position: 'absolute',
    flexDirection: 'column',
    gap: 2,
    bottom: 15,
    left: 15,
    zIndex: 4,
  },
  badgeGroup: {
    position: 'absolute',
    top: -5,
    right: -5,
    minWidth: 28,
    alignItems: 'center',
    backgroundColor: 'green',
  },
  badgeText: {
    color: '#fff',
    fontSize: 14,
  },
  annotations: {
    position: 'absolute',
    flexDirection: 'column',
    gap: 2,
    bottom: 48,
    left: 16,
    zIndex: 3,
  },
  annotationsItem: {
    flexDirection: 'row',
    gap: 2,
  },
  annotationsText: {
    color: '#111',
    fontSize: 15,
  },
  annotationsTextBold: {
    color: '#111',
    fontSize: 15,
    fontWeight: 'bold',
  },
});


function getScrollHandler(props) {
  function handleScroll(e) {
    const {items, loading, meta, entry_point_id} = props;
    if (e.nativeEvent.contentOffset.y + e.nativeEvent.layoutMeasurement.height * 2 > e.nativeEvent.contentSize.height
      && !loading && meta.count > items.length) {
      const {subj_ids, limit, offset, request_options} = meta;
      let options = Object.assign(request_options, {'offset': offset + limit});

      const params = {
      mart_id: entry_point_id,
        options_obj: options,
        append: true,
        subj_ids
      };
      props.notifyLoadingEntities();
      props.getEntities(params)
    }
  }

  return handleScroll;
}


function getColor(mark, defaultColor) {
  const prefixes = ['color-', 'pin-color-'];
  let color = 'gray';
  const colorClass = mark.view_class.find(
    c => prefixes.some(p => c.startsWith(p)));
  if (!colorClass)
    return color;
  for (const p of prefixes) {
    if (colorClass.startsWith(p)) {
      return `#${colorClass.replace(p, '')}`;
    }
  }
  return color;
}


export function useTextState(short_marks) {
  const textState = [], backgroundColorState = [];
  short_marks = short_marks === undefined ? [] : short_marks;
  short_marks.map(mark => {
    if (
      !mark.view_class.includes('hide-in-ribbon') &&
      !mark.view_class.includes('hidden') &&
      !mark.view_class.includes('hide-in-all-and-person-problem')
    ) {
      const text = mark.values.join(', ');
      textState.push(text);
      let color = getColor(mark, 'gray');
      backgroundColorState.push(color);
    }
  });
  return {textState, backgroundColorState};
}

function getGroupName(meta) {
  return (meta && meta.alike && meta.alike.group_name) || null;
}

function getGroupSize(data) {
  return (data.extra && data.extra.group_size) || 0;
}


function getItemGroupName(data) {
  return (getGroupSize(data) && data.extra.group_name) || null;
}


function useGroupOpen(data, meta) {
  const getState = useStore().getState,
    dispatch = useDispatch();

  const groupSize = getGroupSize(data);

  function groupOpen() {
    notifyLoadingEntities()(dispatch);
    expandGroup(data.id, meta)(dispatch, getState);
  }

  return {groupOpen, groupSize};
}


export function useGroupClose(store = null) {
  // useStore won't return the edw store if
  // the hook is used ouside a edw component
  // one can optionally pass the correct store
  const defaultStore = useStore();
  store = store || defaultStore;
  const {dispatch, getState} = store;

  const meta = getState().entities?.items.meta;

  const groupName = getGroupName(meta);

  function groupClose() {
    const {request_options} = meta;
    delete request_options.alike;
    delete request_options.offset;

    const params = {
      mart_id: meta.data_mart.id,
      subj_ids: meta.subj_ids,
      options_obj: request_options,
    };

    notifyLoadingEntities()(dispatch);
    getEntities(params)(dispatch, getState);
  }

  return {groupClose, groupName};
}


function useOnEntityPress(data, meta, fromRoute) {
  const {id, entity_model} = data,
    {navigation} = Singleton.getInstance();
  const {groupOpen, groupSize} = useGroupOpen(data, meta);

  function onPress() {
    if (groupSize)
      groupOpen();
    else
      navigation.navigate('Detail-' + entity_model, {id, fromRoute});
  }

  return {onPress, groupSize};
}


function renderGroupBadge(groupSize, styles) {
  return groupSize
    ? <Badge style={styles.badgeGroup}>
      <Text style={styles.badgeText}>{groupSize}</Text>
    </Badge>
    : null;
}


function useCardShadow(groupSize, numLayers, styles) {
  const topIncrement = 2,
    leftIncrement = 2.5,
    rotateZIncrement = 0.25,
    opacityDecrement = 0.25;

  const size = useRef({width: 0, height: 0}).current;
  const [shadows, setShadows] = useState([]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(updateShadows, [groupSize]);

  function setCardSize(layout) {
    const {width, height} = layout;
    if (size.width !== width || size.height !== height) {
      size.width = width;
      size.height = height;
      updateShadows();
    }
  }

  function updateShadows() {
    if (!groupSize) {
      setShadows([]);
      return;
    }
    const newShadows = [];
    for (let i = 0; i <= numLayers; i++) {
      const style = {
        ...styles.cardShadow,
        ...size,
        top: topIncrement * i,
        left: leftIncrement * i,
        transform: [{rotateZ: `${rotateZIncrement * i}deg`}],
      };
      newShadows.push(<View key={i} style={style} opacity={1 - i * opacityDecrement}/>);
    }
    newShadows.reverse();
    setShadows(newShadows);
  }

  return {shadows, setCardSize};
}


export function renderEntityItem(
  props,
  text,
  styles,
  icon = null,
  customOnPress = null,
  renderAnnotations = false,
) {
  const {data, meta, fromRoute, toRoute, containerSize, items} = props,
    {Domain, navigation} = Singleton.getInstance();

  const {textState, backgroundColorState} = useTextState(data.short_marks);

  const isLastItem = items[items.length - 1].id === data.id;

  let {onPress, groupSize} = useOnEntityPress(data, meta, fromRoute);
  if (customOnPress)
    onPress = customOnPress;

  const {shadows, setCardSize} = useCardShadow(groupSize, 2, styles);

  const groupName = getItemGroupName(data);
  if (groupName)
    text = groupName;

  const templateIsDataMart = props.templateIsDataMart === undefined
    ? true : props.templateIsDataMart;

  let match;
  if ((match = data.media.match(mediaRegExp)))
    data.media = `${Domain}/${match[2].replace(/^\//, '')}`;

  let cardContainerStyle,
    cardImageContainerStyle,
    imageBackgroundStyle,
    textStyle,
    navigateToDMCardStyle;

  if (templateIsDataMart) {
    cardContainerStyle = styles.cardContainer;
    cardImageContainerStyle = styles.cardImageContainer;
    imageBackgroundStyle = styles.imageBackground;
    textStyle = styles.entityNameText;
  } else {
    if (containerSize !== RELATED_CONTAINER_SIZE.large) {
      cardContainerStyle = styles.cardContainerRelated;
      cardImageContainerStyle = styles.cardImageContainerRelated;
      imageBackgroundStyle = styles.imageBackgroundRelated;
      textStyle = {...styles.entityNameText, fontSize: 16};
      navigateToDMCardStyle = {...styles.navigateToDMCardStyle, height: 150}
    } else {
      const height = 256;
      cardContainerStyle = {...styles.cardContainerRelated, height};
      cardImageContainerStyle = {...styles.cardImageContainerRelated, height};
      imageBackgroundStyle = {...styles.imageBackgroundRelated, height};
      textStyle = styles.entityNameText;
      navigateToDMCardStyle = {...styles.navigateToDMCardStyle, height}
    }
  }

  const annotations = {};
  let badgeTextLimit = 12;
  if (renderAnnotations) {
    if (data.extra) {
      for (const [key, val] of Object.entries(data.extra)) {
        if (val instanceof Object && 'name' in val && 'value' in val)
          annotations[key] = val;
      }
    }
    const characteristics = data.short_characteristics || [];
    for (const c of characteristics) {
      const a = {};
      a['name'] = c.name;
      a['value'] = c.values.join(', ');
      annotations[c.path] = a;
      badgeTextLimit = 30;
    }
  }

  return (
    <>
      <Card appearance="filled" onPress={onPress} style={cardContainerStyle}>
        {shadows}
        <View onLayout={e => setCardSize(e.nativeEvent.layout)} style={cardImageContainerStyle}>
          <ImageBackground
            source={data.media ? {uri: data.media} : null}
            style={imageBackgroundStyle || {}}>
            <Text style={textStyle}>{text}{icon}</Text>

            <View style={styles.annotations}>
              {Object.keys(annotations).map((t, i) => {
                return (
                  <View key={t + i} style={styles.annotationsItem} >
                    <Text style={styles.annotationsTextBold}>
                      {annotations[t].name}:
                    </Text>
                    <Text style={styles.annotationsText}>
                      {annotations[t].value}
                    </Text>
                  </View>
                );
              })}
            </View>

            <View style={styles.badge}>
              {textState.length ? textState.map((t, i) => (
                <Badge key={i} style={{backgroundColor: backgroundColorState[i]}}>
                  <Text style={styles.badgeText}>
                    {t.length > badgeTextLimit ? `${t.slice(0, badgeTextLimit)}...` : t}
                  </Text>
                </Badge>
               )) : null
              }
            </View>
          </ImageBackground>
        </View>
        {renderGroupBadge(groupSize, styles)}
      </Card>
      {isLastItem && !templateIsDataMart &&
        <Card appearance="filled" style={navigateToDMCardStyle} onPress={() => navigation.navigate(toRoute)}>
          <View style={styles.navigateToDMViewStyle}>
            <Text>Еще</Text>
          </View>
        </Card>
      }
    </>
  )
}


export function renderEntityTile(props, styles, createItem) {
  const handleScroll = getScrollHandler(props);
  const {items, loading} = props;

  const scrollRef = useRef();

  const scrollToTop = () => {
    scrollRef.current?.scrollTo({
      y: 0,
      animated: true,
    });
  }

  const instance = Singleton.getInstance();
    instance.scrollToTop = scrollToTop;

  return (
    <ScrollView
      ref={scrollRef}
      scrollEventThrottle={2000}
      onScroll={e => handleScroll(e)}>
      {loading ?
        <View style={styles.spinnerContainer}>
          <Spinner visible={true}/>
        </View>
        : null
      }
      <Layout style={styles.layout}>{items.map(createItem)}</Layout>
    </ScrollView>
  );
}


export function renderEntityList(props, styles, createItem) {
  const {items, templateIsDataMart, dataMartName, containerSize} = props;

  if (templateIsDataMart)
    return renderEntityTile(props, styles, createItem);

  if (!items.length)
    return null;

  let containerRelatedViewStyle;
  if (containerSize !== RELATED_CONTAINER_SIZE.large)
    containerRelatedViewStyle = styles.containerRelatedView;
  else
    containerRelatedViewStyle = {...styles.containerRelatedView, height: 300};

  return (
    <View style={containerRelatedViewStyle}>
      <Text style={styles.containerRelatedViewName}>{dataMartName}</Text>
      <List
        style={styles.containerRelated}
        contentContainerStyle={styles.containerContentRelated}
        horizontal={true}
        showsHorizontalScrollIndicator={false}
        data={items}
        renderItem={info => createItem(info.item, info.index)}
      />
    </View>
  )
}
