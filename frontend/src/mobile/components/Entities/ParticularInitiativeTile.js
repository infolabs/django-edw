import React, {Component} from 'react'
import {ScrollView, View, ImageBackground, StyleSheet} from 'react-native'
import {Text, Card, Layout} from '@ui-kitten/components'
import {Badge} from 'native-base'
import Singleton from '../../utils/singleton'
import Spinner from 'react-native-loading-spinner-overlay';
import {tileStyles} from "../../styles/entities";
import EntityMixin from "../BaseEntities/EntityMixin";


const stylesComponent = StyleSheet.create({
  badge: {
    position: 'absolute',
    bottom: 15,
    left: 15,
    zIndex: 4
  },
  badgeText: {
    color: '#fff'
  }
});

const styles = Object.assign(tileStyles, stylesComponent);

export default class ParticularInitiativeTile extends EntityMixin(Component) {
  render() {
    const {items, loading} = this.props;
    const instance = Singleton.getInstance();

    return (
      <ScrollView scrollEventThrottle={2000}
                  onScroll={e => this.handleScroll(e)}>
        {loading ?
          <View style={styles.spinnerContainer}>
            <Spinner visible={true}/>
          </View>
          : null
        }
        <Layout style={styles.layout}>
          {items.map(
            (child, i) => <ParticularInitiativeTileItem key={i} data={child} domain={instance.Domain}
                                                        maxLengthDescriptionTile={this.maxLengthDescriptionTile}/>
          )}
        </Layout>
      </ScrollView>
    );
  }
}

class ParticularInitiativeTileItem extends Component {
  render() {
    const {data, domain, maxLengthDescriptionTile} = this.props,
      {short_marks} = data;

    if (data.media.match(/.*<img.*?src=('|")(.*?)('|")/))
      data.media = `${domain}/${data.media.match(/.*<img.*?src=('|")(.*?)('|")/)[2]}`;

    let textState = null,
      backgroundColorState = 'gray';

    short_marks.map(mark => {
      if (mark.name === "Состояние" || mark.name === "Системное состояние") {
        textState = mark.values[0];
        mark.view_class.map(item => {
          if (item.startsWith('pin-color-'))
            backgroundColorState = `#${item.replace('pin-color-', '')}`;
        })
      }
    });

    return (
      <Card style={styles.cardContainer} onPress={() => console.log(data.id)}>
        <View style={styles.cardImageContainer}>
          <ImageBackground source={{uri: data.media}} style={styles.imageBackground}>
            <Text style={styles.entityNameText}>
              {data.entity_name.length > maxLengthDescriptionTile ?
                `${data.entity_name.slice(0, maxLengthDescriptionTile)}...`
                : data.entity_name
              }
            </Text>
            {textState ?
              <Badge style={{...styles.badge, backgroundColor: backgroundColorState}}>
                <Text style={styles.badgeText}>
                  {textState.length > 12 ?
                    `${textState.slice(0, 12)}...`
                    : textState
                  }
                </Text>
              </Badge>
              : null
            }
          </ImageBackground>
        </View>
      </Card>
    )
  }
}
