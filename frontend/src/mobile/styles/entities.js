import {StyleSheet} from 'react-native';
import platformSettings from "../constants/Platform";


const {deviceHeight, deviceWidth} = platformSettings;

export const tileStyles = StyleSheet.create({
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

export const listStyles = StyleSheet.create({
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
    fontSize: 18,
    textShadowColor: '#333',
    textShadowRadius: 5
  }
});
