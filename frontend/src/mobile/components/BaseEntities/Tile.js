import React, {Component} from 'react'
import {ScrollView, View, ImageBackground, StyleSheet} from 'react-native'
import {Text, Card, Layout} from '@ui-kitten/components'
import platformSettings from "../../constants/Platform";


const {deviceHeight, deviceWidth} = platformSettings;

const styles = StyleSheet.create({
  layout: {
    flex: 1,
    alignItems: 'center',
    width: deviceWidth,
    paddingHorizontal: 16,
  },
  cardContainer: {
    width: '100%',
    minHeight: 200,
    marginHorizontal: 5,
    marginVertical: 5,
    borderRadius: 15,
  },
  cardImageContainer: {
    ...StyleSheet.absoluteFillObject,
  },
  imageBackground:{
    ...StyleSheet.absoluteFillObject,
    height: 200,
  },
  entityNameText: {
    color: '#fff',
    fontWeight: '500',
    backgroundColor: 'rgba(0,0,0,0.3)',
    height: '100%',
    width: '100%',
    paddingHorizontal: 15,
    paddingVertical: 10,
    fontSize: 20
  }
});

export default class Tile extends Component {
  render() {
    const {items} = this.props;

    return (
      <ScrollView>
        <Layout style={styles.layout}>
          {items.map(
            (child, i) => <TileItem key={i} data={child}/>
          )}
        </Layout>
      </ScrollView>
    );
  }
}

class TileItem extends Component {
  render(){
    const {data} = this.props;

    // ПОПРАВИТЬ УРЛ!!!
    if(data.media.match(/.*<img.*?src=('|")(.*?)('|")/))
      data.media = `https://narod-expert.ru/${data.media.match(/.*<img.*?src=('|")(.*?)('|")/)[2]}`;

    return(
      <Card style={styles.cardContainer}>
        <View style={styles.cardImageContainer}>
          <ImageBackground source={{uri: data.media}} style={styles.imageBackground}>
            <Text style={styles.entityNameText}>{data.entity_name}</Text>
          </ImageBackground>
        </View>
      </Card>
    )
  }
}
