import {StyleSheet} from 'react-native';


export const filtersStyles = StyleSheet.create({
  filteredView: {
    paddingTop: 5,
  },
  filteredBadge: {
    width: 12,
    height: 12,
    backgroundColor: 'blue',
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute',
    top: -2,
    right: -3,
  },
  filteredBadgeText: {
    fontSize: 9,
    color: '#fff',
  },
});
