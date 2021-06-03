import React from 'react';
import {Icon} from 'native-base';
import Swiper from 'react-native-swiper';
import {View, Image} from 'react-native';
import {Text, TopNavigation} from '@ui-kitten/components';
import HTML from 'react-native-render-html';
import {dataMartStyles as styles} from '../../styles/dataMarts';


function useDetail(props) {

  // HACK. Свойство onPress у TopNavigationAction не работает.
  // Поэтому пришлось использовать иконку с native-base
  function closeDetailView() {
    return <Icon onPress={() => props.hideVisibleDetail()} name="close" />;
  }

  function getNavigation(title = 'Объект') {
    const {data} = props;
    const style = {...styles.navigationTitle, backgroundColor: '#fff'};
    return (
      <TopNavigation
        alignment="center"
        title={() => <Text
          style={style}>
          {`${title} № ${data.id}`}
        </Text>}
        accessoryRight={closeDetailView}
      />
    );
  }

  function getMedia() {
    const {data} = props;
    const style = {fontSize: 52, color: '#000'};
    if (data.media.length === 1){
      return (
        <View style={styles.slide}>
          <Image style={styles.imageSlide} source={{uri: data.media[0]}}/>
        </View>
      );
    } else if (data.media.length > 1) {
      return (
        <Swiper style={styles.swipeWrapper} showsButtons={data.media.length > 1} loop
                activeDotColor={'#000'} dotColor={'#fff'}
                prevButton={<Text style={style}>‹</Text>}
                nextButton={<Text style={style}>›</Text>}
                autoplayTimeout={5} autoplay>
          {data.media.map((item, key) =>
            <View key={key} style={styles.slide}>
              <Image style={styles.imageSlide} source={{uri: item}}/>
            </View>
          )}
        </Swiper>
      );
    } else
      return null;
  }

  function getContent() {
    const {data} = props;

    const viewStyles = {
      name: {fontWeight: 'normal'},
      description: {marginVertical: 12},
      html: {fontSize: 16},
      values: {fontWeight: 'bold'},
    };
    return (
      <View style={styles.infoEntity}>
        <Text
          style={viewStyles.name}
          category="h5">
          {data.entity_name}
        </Text>
        <View style={viewStyles.description}>
          <HTML source={{html: data.description || '<p/>'}} baseFontStyle={viewStyles.html}/>
        </View>
        {data.characteristics.map((item, key) =>
          <Text key={key}><Text style={viewStyles.values}>{item.name}:</Text> {item.values[0]}</Text>
        )}
      </View>
    );
  }

  return {
    getNavigation,
    getMedia,
    getContent,
  };
}


export default useDetail;
