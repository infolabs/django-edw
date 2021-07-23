import React, {useState, useRef, useEffect} from 'react';
import {useDispatch, useStore} from 'react-redux';
import {
  expandGroup,
  notifyLoadingEntities,
  getEntities,
} from '../../actions/EntitiesActions';

import {ScrollView, View, ImageBackground, StyleSheet} from 'react-native';
import Spinner from 'react-native-loading-spinner-overlay';
import {Badge} from 'native-base';
import {Text, Card, Layout, List} from '@ui-kitten/components';
import Singleton from '../../utils/singleton';

export const maxLengthDescriptionTile = 70;
export const maxLengthDescriptionListRelated = 90;
const mediaRegExp = /.*<img.*?src=(['"])(.*?)(['"])/;

export const stylesComponent = StyleSheet.create({
  badge: {
    position: 'absolute',
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
  },
});


function getScrollHandler(props) {
  function handleScroll(e) {
    const {items, loading, meta} = props;
    if (e.nativeEvent.contentOffset.y + e.nativeEvent.layoutMeasurement.height * 2
      > e.nativeEvent.contentSize.height
      && !loading && meta.count > items.length) {
      const {subj_ids, limit, offset, request_options} = meta;
      let options = Object.assign(request_options, {'offset': offset + limit});
      props.notifyLoadingEntities();
      props.getEntities(props.entry_point_id, subj_ids, options, [], true);
    }
  }
  return handleScroll;
}


function getColor(item, backgroundColorState) {
  const prefixes = ['color-', 'pin-color-'];
  for (const p of prefixes) {
    if (item.startsWith(p))
      backgroundColorState = `#${item.replace(p, '')}`;
  }
  return backgroundColorState;
}


export function useTextState(short_marks) {
  let textState = null, backgroundColorState = 'gray';

  short_marks = short_marks === undefined ? [] : short_marks;

  short_marks.map(mark => {
    if (mark.name === 'Состояние' || mark.name === 'Системное состояние') {
      textState = mark.values[0];
      mark.view_class.map(item => {
        backgroundColorState = getColor(item, backgroundColorState);
      });
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
  store = store ? store : defaultStore;
  const {dispatch, getState} = store;

  const meta = getState().entities && getState().entities.items.meta;

  const groupName = getGroupName(meta);

  function groupClose(e) {
    const request_options = meta.request_options;
    delete request_options.alike;
    delete request_options.offset;

    notifyLoadingEntities()(dispatch);
    getEntities(meta.data_mart.id, meta.subj_ids, request_options)(dispatch, getState);
  }

  return {groupClose, groupName};
}


function useOnEntityPress(data, meta) {
  const {id, entity_model} = data,
        {navigation} = Singleton.getInstance();

  const {groupOpen, groupSize} = useGroupOpen(data, meta);

  function onPress(event) {
    if (groupSize)
      groupOpen();
    else
      navigation.navigate('Detail-' + entity_model, {id});
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
        transform: [{ rotateZ: `${rotateZIncrement * i}deg` }],
      };
      newShadows.push(<View key={i} style={style} opacity={1 - i * opacityDecrement}/>);
    }
    newShadows.reverse();
    setShadows(newShadows);
  }

  return {shadows, setCardSize};
}


export function renderEntityItem(props, text, badge, styles) {
  const {data, meta} = props,
    {Domain} = Singleton.getInstance();
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const {onPress, groupSize} = useOnEntityPress(data, meta);
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const {shadows, setCardSize} = useCardShadow(groupSize, 2, styles);

  const groupName = getItemGroupName(data);
  if (groupName)
    text = groupName;

  const templateIsDataMart = props.templateIsDataMart === undefined
    ? true : props.templateIsDataMart;

  let match;
  if ((match = data.media.match(mediaRegExp)))
    data.media = `${Domain}/${match[2].replace(/^\//, '')}`;

  const textStyle = templateIsDataMart
    ? {...styles.entityNameText}
    : {...styles.entityNameText, fontSize: 16};

  return <Card
    appearance="filled"
    onPress={onPress}
    style={templateIsDataMart ? styles.cardContainer : styles.cardContainerRelated}>
    {shadows}
    <View
      onLayout={e => {setCardSize(e.nativeEvent.layout);}}
      style={templateIsDataMart ? styles.cardImageContainer : styles.cardImageRelated}>
          <ImageBackground
            source={data.media ? {uri: data.media } : null}
            style={templateIsDataMart ? styles.imageBackground : styles.imageBackgroundRelated}>
            <Text style={textStyle}>{text}</Text>
            {badge}
          </ImageBackground>
    </View>
    {renderGroupBadge(groupSize, styles)}
  </Card>;
}


export function renderEntityTile(props, styles, createItem) {
  const handleScroll = getScrollHandler(props);
  const {items, loading} = props;

  return <ScrollView
      scrollEventThrottle={2000}
      onScroll={e => handleScroll(e)}>
      {loading ?
        <View style={styles.spinnerContainer}>
          <Spinner visible={true}/>
        </View>
        : null
      }
      <Layout style={styles.layout}>{items.map(createItem)}</Layout>
  </ScrollView>;
}


export function renderEntityList(props, styles, createItem) {
  const {items, templateIsDataMart} = props;

  return templateIsDataMart
    ? renderEntityTile(props, styles, createItem)
    : <List
        style={styles.containerRelated}
        contentContainerStyle={styles.containerContentRelated}
        horizontal={true}
        showsHorizontalScrollIndicator={false}
        data={items}
        renderItem={info => createItem(info.item, info.index)}
      />;
}
