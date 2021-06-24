import React from 'react';
import {Icon} from "native-base";
import Swiper from 'react-native-swiper';
import {View, Image} from 'react-native';
import {Text, TopNavigation} from "@ui-kitten/components";
import HTML from 'react-native-render-html';
import {dataMartStyles as styles} from "../../native_styles/dataMarts";

const BaseDetail = Base => class extends Base {

  // HACK. Свойство onPress у TopNavigationAction не работает. Поэтому пришлось использовать иконку с native-base
  closeDetailView = () => (
    <Icon onPress={() => this.props.hideVisibleDetail()} name='close'/>
  );

  getNavigation = (title = "Объект") => {
    const {data} = this.props;
    return (
      <TopNavigation
        alignment='center'
        title={() => <Text
          style={{...styles.navigationTitle, backgroundColor: "#fff"}}>
          {`${title} № ${data.id}`}
        </Text>}
        accessoryRight={this.closeDetailView}
      />
    )
  };

  getMedia = () => {
    const {data} = this.props;
    if (data.media.length === 1){
      return(
        <View style={styles.slide}>
          <Image style={styles.imageSlide} source={{uri: data.media[0]}}/>
        </View>
      );
    } else if (data.media.length > 1) {
      return(
        <Swiper style={styles.swipeWrapper} showsButtons={data.media.length > 1} loop
                activeDotColor={"#000"} dotColor={"#fff"}
                prevButton={<Text style={{fontSize: 52, color: "#000"}}>‹</Text>}
                nextButton={<Text style={{fontSize: 52, color: "#000"}}>›</Text>}
                autoplayTimeout={5} autoplay>
          {data.media.map((item, key) =>
            <View key={key} style={styles.slide}>
              <Image style={styles.imageSlide} source={{uri: item}}/>
            </View>
          )}
        </Swiper>
      )
    } else {
      return null
    }
  };

  getContent = () => {
    const {data} = this.props;
    return (
      <View style={styles.infoEntity}>
        <Text
          style={{fontWeight: 'normal'}}
          category='h5'>
          {data.entity_name}
        </Text>
        <View style={{marginVertical: 12}}>
          <HTML source={{html: data.description || '<p/>'}} baseFontStyle={{fontSize: 16}}/>
        </View>
        {data.characteristics.map((item, key) =>
          <Text key={key}><Text style={{fontWeight: 'bold'}}>{item.name}:</Text> {item.values[0]}</Text>
        )}
      </View>
    )
  }
};

export default BaseDetail
