import {StyleSheet} from 'react-native';
import platformSettings from '../constants/Platform';


const {deviceHeight, deviceWidth} = platformSettings;

export const tileStyles = StyleSheet.create({
  spinnerContainer: {
    height: deviceHeight,
    width: deviceWidth,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'absolute',
  },
  layout: {
    width: deviceWidth,
    paddingHorizontal: 10,
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  cardContainer: {
    width: deviceWidth / 2 - 26, // marginHorizontal * 2 + layout.paddingHorizontal = 26
    minHeight: 260,
    marginVertical: 8,
    marginHorizontal: 8,
    overflow: 'visible',
  },
  cardImageContainer: {
    ...StyleSheet.absoluteFillObject,
    minHeight: 260,
    borderWidth: 1,
    borderColor: '#959595',
    borderRadius: 15,
    overflow: 'hidden',
  },
  cardShadow: {
    position: 'absolute',
    borderColor: '#888',
    borderWidth: 1,
    borderRadius: 15,
    backgroundColor: '#aaa',
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
    flexWrap: 'wrap',
  },
});

export const listStyles = StyleSheet.create({
  spinnerContainer: {
    height: deviceHeight,
    width: deviceWidth,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'absolute',
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
    overflow: 'visible',
  },
  cardShadow: {
    position: 'absolute',
    borderColor: '#888',
    borderWidth: 1,
    borderRadius: 15,
    backgroundColor: '#aaa',
  },
  cardImageContainer: {
    ...StyleSheet.absoluteFillObject,
    borderColor: '#959595',
    borderWidth: 1,
    borderRadius: 15,
    minHeight: 200,
    overflow: 'hidden',
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
    textShadowRadius: 5,
  },
  containerRelated: {
    backgroundColor: 'transparent',
    height: 160,
  },
  containerContentRelated: {
    marginVertical: 25,
    marginHorizontal: 8,
  },
  cardContainerRelated: {
    width: 256,
    height: 150,
    marginHorizontal: 5,
    borderRadius: 15,
  },
  cardImageRelated: {
    ...StyleSheet.absoluteFillObject,
  },
  imageBackgroundRelated: {
    ...StyleSheet.absoluteFillObject,
    height: 150,
  },
});
