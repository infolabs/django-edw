import React, {Component} from 'react'
import {ScrollView, View, ImageBackground, StyleSheet} from 'react-native'
import {Text, Card, Layout} from '@ui-kitten/components'
import platformSettings from "../../constants/Platform";
import Singleton from '../../utils/singleton'
import Spinner from 'react-native-loading-spinner-overlay';


const {deviceHeight, deviceWidth} = platformSettings;

const styles = StyleSheet.create({
  spinnerContainer: {
    height: deviceHeight,
    width: deviceWidth,
    justifyContent: 'center',
    alignItems: 'center',
  },
  layout: {
    width: deviceWidth,
    paddingHorizontal: 10,
    flexDirection: 'row',
    flexWrap: 'wrap'
  },
  cardContainer: {
    width: deviceWidth/2 - 26, // marginHorizontal * 2 + layout.paddingHorizontal = 26
    minHeight: 260,
    marginVertical: 8,
    marginHorizontal: 8,
    borderRadius: 15,
  },
  cardImageContainer: {
    ...StyleSheet.absoluteFillObject,
  },
  imageBackground:{
    ...StyleSheet.absoluteFillObject,
    height: 260,
  },
  entityNameText: {
    color: '#fff',
    fontWeight: '500',
    backgroundColor: 'rgba(0,0,0,0.3)',
    height: '100%',
    width: '100%',
    paddingHorizontal: 15,
    paddingVertical: 10,
    fontSize: 18,
    textShadowColor: '#333',
    textShadowRadius: 5,
    flexWrap: 'wrap'
  }
});

export default class Tile extends Component {
  render() {
    const {items, loading} = this.props;
    const instance = Singleton.getInstance();

    if (loading) {
      return (
        <View style={styles.spinnerContainer}>
          <Spinner visible={true}/>
        </View>
      )
    } else {
      return (
        <ScrollView>
          <Layout style={styles.layout}>
            {items.map(
              (child, i) => <TileItem key={i} data={child} domain={instance.Domain}/>
            )}
          </Layout>
        </ScrollView>
      );
    }
  }
}

class TileItem extends Component {
  render(){
    const {data, domain} = this.props;

    if(data.media.match(/.*<img.*?src=('|")(.*?)('|")/))
      data.media = `${domain}/${data.media.match(/.*<img.*?src=('|")(.*?)('|")/)[2]}`;

    return(
      <Card style={styles.cardContainer}>
        <View style={styles.cardImageContainer}>
          <ImageBackground source={{uri: data.media}} style={styles.imageBackground}>
            <Text style={styles.entityNameText}>
              {data.entity_name.length > 90 ?
                `${data.entity_name.slice(0, 90)}...`
                : data.entity_name
              }
            </Text>
          </ImageBackground>
        </View>
      </Card>
    )
  }
}
