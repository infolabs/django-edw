import React from 'react';
import {ScrollView, View, ImageBackground} from 'react-native';
import {Text, Card, Layout} from '@ui-kitten/components';
import Singleton from '../../utils/singleton';
import Spinner from 'react-native-loading-spinner-overlay';
import {tileStyles as styles} from '../../styles/entities';
import useEntities from './useEntities';


function Tile(props) {
    const {items, loading, loadingEntity, getEntity} = props;
    const [maxLengthDescriptionTile, handleScroll] = useEntities(props);
    const instance = Singleton.getInstance();

    return (
      <ScrollView scrollEventThrottle={2000}
                  onScroll={e => handleScroll(e)}>
        {loading || loadingEntity ?
          <View style={styles.spinnerContainer}>
            <Spinner visible={true}/>
          </View>
          : null
        }
        <Layout style={styles.layout}>
          {items.map(
            (child, i) => <TileItem key={i} data={child} domain={instance.Domain} getEntity={getEntity}
                                    maxLengthDescriptionTile={maxLengthDescriptionTile}/>
          )}
        </Layout>
      </ScrollView>
    );
}


function TileItem(props) {
  const {data, domain, maxLengthDescriptionTile} = props;

  if (data.media.match(/.*<img.*?src=(['"])(.*?)(['"])/))
    data.media = `${domain}/${data.media.match(/.*<img.*?src=(['"])(.*?)(['"])/)[2]}`;

  return (
    <Card style={styles.cardContainer} onPress={() => props.getEntity(data)}>
      <View style={styles.cardImageContainer}>
        <ImageBackground source={{uri: data.media}} style={styles.imageBackground}>
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
