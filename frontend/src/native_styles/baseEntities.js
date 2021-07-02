import {StyleSheet} from 'react-native';
import platformSettings from '../constants/Platform';


const {deviceHeight, deviceWidth} = platformSettings;

export const baseEntitiesStyles = StyleSheet.create({
  spinnerContainer: {
    height: deviceHeight,
    width: deviceWidth,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'absolute',
  },
});
