import React from 'react';
import {ScrollView, View, ImageBackground, StyleSheet} from 'react-native';
import Spinner from 'react-native-loading-spinner-overlay';
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


export function renderEntityItem(props, text, badge, styles) {
  const {data} = props,
    {id, entity_model} = data,
    {Domain, navigation} = Singleton.getInstance();

  const templateIsDataMart = props.templateIsDataMart === undefined
    ? true : props.templateIsDataMart;

  if (data.media.match(mediaRegExp))
    data.media = `${Domain}/${data.media.match(mediaRegExp)[2]}`;

  function onPress(event) {
    navigation.navigate('Detail-' + entity_model, {id});
  }

  const textStyle = templateIsDataMart
    ? {...styles.entityNameText}
    : {...styles.entityNameText, fontSize: 16};

  return <Card
           style={templateIsDataMart ? styles.cardContainer : styles.cardContainerRelated}
           onPress={onPress}>
      <View style={templateIsDataMart ? styles.cardImageContainer : styles.cardImageRelated}>
        <ImageBackground
          source={data.media ? {uri: data.media } : null}
          style={templateIsDataMart ? styles.imageBackground : styles.imageBackgroundRelated}>
          <Text style={textStyle}>{text}</Text>
          {badge}
        </ImageBackground>
      </View>
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
      renderItem={(child, i) => createItem(child, i)}
    />;
}
