import React, { Component } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Header from '../components/Header';
import TermsTree from '../components/TermsTree';
import Entities from '../components/Entities';
import MainSection from '../components/MainSection';
import * as TodoActions from '../actions/TodoActions';

class TodoApp extends Component {

  componentDidMount() {
    this.props.actions.getTodos();
  }

  render() {
    const { todos, actions } = this.props;

    return (
      <div>
        <div className="terms-tree-container">
          <TermsTree />
          <Entities />
        </div>

        <Header addTodo={actions.addTodo} />
        <MainSection todos={todos} actions={actions} />
      </div>
    );
  }
}

function mapState(state) {
  return {
    todos: state.todos
  };
}

function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(TodoActions, dispatch)
  };
}

export default connect(mapState, mapDispatch)(TodoApp);
