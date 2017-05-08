import { createStore, compose, applyMiddleware } from 'redux';
// import promise from 'redux-promise';
import thunkMiddleware from 'redux-thunk';
import { persistState } from 'redux-devtools';
import rootReducer from 'reducers';
import DevTools from 'components/DevTools'

// import { saveStore } from './globalStore'

const enhancer = compose(
    // applyMiddleware(promise),
    applyMiddleware(thunkMiddleware),
    DevTools.instrument(),
    persistState(
        window.location.href.match(
            /[?&]debug_session=([^&#]+)\b/
        )
    )
);

export default function configureStore(initialState) {
    const store = createStore(rootReducer, initialState, enhancer);

    if (module.hot) {
        module.hot.accept('../reducers', () =>
            store.replaceReducer(require('../reducers').default)
        );
    }

    // mart_id = dom_attrs.getNamedItem('data-data-mart-pk').value
    // saveStore(store);

    return store;
}
