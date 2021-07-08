import React from 'react';
import {ScrollView, View, ImageBackground} from 'react-native';
import {Text, Card, Layout} from '@ui-kitten/components';
import Singleton from '../../utils/singleton';
import Spinner from 'react-native-loading-spinner-overlay';
import {tileStyles as styles} from '../../native_styles/entities';
import useEntities from './useEntities';


function Tile(props) {
  const [maxLengthDescriptionTile, handleScroll] = useEntities(props);
  const {items, loading} = props;
  const instance = Singleton.getInstance();
  const {Domain} = instance;

  return (
    <ScrollView scrollEventThrottle={2000}
                onScroll={e => handleScroll(e)}>
      {loading ?
        <View style={styles.spinnerContainer}>
          <Spinner visible={true}/>
        </View>
        : null
      }
      <Layout style={styles.layout}>
        {items.map(
          (child, i) => <TileItem key={i} data={child} domain={Domain}
                                  maxLengthDescriptionTile={maxLengthDescriptionTile}/>
        )}
      </Layout>
    </ScrollView>
  );
}


function TileItem(props) {
  const {data, domain, maxLengthDescriptionTile} = props;

  const mediaRe = /.*<img.*?src=(['"])(.*?)(['"])/;
  if (data.media.match(mediaRe))
    data.media = `${domain}/${data.media.match(mediaRe)[2]}`;

  return (
    <Card style={styles.cardContainer} onPress={() => {}}>
      <View style={styles.cardImageContainer}>
        <ImageBackground source={data.media ? {uri: data.media } : null} style={styles.imageBackground}>
          <Text style={styles.entityNameText}>
            {data.entity_name.length > maxLengthDescriptionTile ?
              `${data.entity_name.slice(0, maxLengthDescriptionTile)}...`
              : data.entity_name
            }
          </Text>
        </ImageBackground>
      </View>
    </Card>
  );
}


export default Tile;
