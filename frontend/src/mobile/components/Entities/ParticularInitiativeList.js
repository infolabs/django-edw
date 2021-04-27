import React, {Component} from 'react'
import {ScrollView, View, ImageBackground, StyleSheet} from 'react-native'
import {Text, Card, Layout} from '@ui-kitten/components'
import platformSettings from "../../constants/Platform"
import {Badge} from 'native-base'
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
  },
  badge: {
    position: 'absolute',
    bottom: 15,
    left: 15,
    zIndex: 4
  }
});

export default class ParticularInitiativeList extends Component {
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
              (child, i) => <ParticularInitiativeListItem key={i} data={child} domain={instance.Domain}/>
            )}
          </Layout>
        </ScrollView>
      );
    }
  }
}

class ParticularInitiativeListItem extends Component {
  render(){
    const {data, domain} = this.props,
          {short_marks} = data;

    if(data.media.match(/.*<img.*?src=('|")(.*?)('|")/))
      data.media = `${domain}/${data.media.match(/.*<img.*?src=('|")(.*?)('|")/)[2]}`;

    let textState = null,
        backgroundColorState = 'gray';

    short_marks.map(mark => {
      if (mark.name === "Состояние"){
        textState = mark.values;
        mark.view_class.map(item => {
          if(item.startsWith('pin-color-'))
            backgroundColorState = `#${item.replace('pin-color-','')}`;
        })
      }
    });

    if (!textState){
      short_marks.map(mark => {
        if (mark.name === "Системное состояние") {
          textState = mark.values;
          mark.view_class.map(item => {
            if (item.startsWith('pin-color-'))
              backgroundColorState = `#${item.replace('pin-color-', '')}`;
          })
        }
      })
    }

    return(
      <Card style={styles.cardContainer} onPress={() => console.log(data.id)}>
        <View style={styles.cardImageContainer}>
          <ImageBackground source={{uri: data.media}} style={styles.imageBackground}>
            <Text style={styles.entityNameText}>{data.entity_name}</Text>
            {textState ?
              <Badge style={{...styles.badge, backgroundColor: backgroundColorState}}>
                <Text style={{color: '#fff'}}>{textState}</Text>
              </Badge>
              : null
            }
          </ImageBackground>
        </View>
      </Card>
    )
  }
}
