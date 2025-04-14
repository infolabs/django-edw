import React from 'react';
import { connect } from 'react-redux';

class NoDataTemplate extends React.Component {
    render() {
        return (
            <div className="ex-no-data">
                <div className="ex-no-data__content">
                    <div className="ex-no-data__icon-wrapper">
                        <div className="ex-no-data__icon" />
                    </div>
                    <div className="ex-no-data__message-wrapper">
                        <div className="ex-no-data__message" />
                    </div>
                </div>
            </div>
        );
    }
}

function mapState(state) {
    return {
        entities: state.entities,
    };
}

export default connect(mapState)(NoDataTemplate); 