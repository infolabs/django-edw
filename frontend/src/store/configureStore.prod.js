import { createStore, applyMiddleware } from 'redux';
// import promise from 'redux-promise';
import thunkMiddleware from 'redux-thunk';
import rootReducer from 'reducers';

// import { saveStore } from './globalStore'

export default function configureStore(initialState) {
    // const store = createStore(rootReducer, initialState, applyMiddleware(promise));
    const store = createStore(rootReducer, initialState, applyMiddleware(thunkMiddleware));

    // mart_id = dom_attrs.getNamedItem('data-data-mart-pk').value
    // saveStore(store);
    return store;
}
