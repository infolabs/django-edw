import {StyleSheet} from 'react-native';


export const termsTreeItemStyles = StyleSheet.create({
  treeContainer: {
    marginLeft: 10,
  },
  termChildren: {
    marginLeft: 23,
    marginTop: 2,
    marginBottom: 4,
  },
  termView: {
    width: 250,
    marginVertical: 4,
  },
  termIsLimb: {
    fontSize: 16,
    display: 'flex',
    flexWrap: 'wrap',
    fontWeight: 'bold',
  },
  term: {
    fontSize: 16,
    display: 'flex',
    flexWrap: 'wrap',
  },
  iconReset: {
    top: 1,
    marginLeft: 6,
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2980b9',
  },
  termIsLimbOrAndView: {
    flexDirection: 'row',
    alignItems: 'center',
    width: 250,
  },
  termIsLimbOrAndIcon: {
    marginLeft: 3,
    marginRight: 7,
    fontSize: 22,
  },
  radio: {
    display: 'flex',
    alignItems: 'flex-start',
  },
  checkbox: {
    display: 'flex',
    alignItems: 'flex-start',
  },
});
