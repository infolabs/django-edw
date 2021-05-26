import { notifyLoadingEntities, getEntities } from '../../actions/EntityActions';
import { useDispatch } from 'react-redux';


const maxLengthDescriptionTile = 70;


function useEntities(props)
{
  const dispatch = useDispatch();

  function handleScroll(e) {
    const {items, loading, meta, entry_point_id} = props;

    if (e.nativeEvent.contentOffset.y + e.nativeEvent.layoutMeasurement.height * 2
        > e.nativeEvent.contentSize.height && !loading && meta.count > items.length) {

      const {subj_ids, limit, offset, request_options} = meta;
      let options = Object.assign(request_options, {'offset': offset + limit});

      notifyLoadingEntities()(dispatch);
      getEntities(entry_point_id, subj_ids, options)(dispatch);
    }
  }

  return [maxLengthDescriptionTile, handleScroll];
}

export default useEntities;
