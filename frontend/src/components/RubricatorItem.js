import React, { Component, PropTypes } from 'react';

export default class RubricatorItem extends Component {
  static propTypes = {
    term: PropTypes.object.isRequired
  };

  render() {

    const { term, actions } = this.props;

    let inp_type = false;

    switch (term.method) {
      case 'facet':
        inp_type = 'radio';
        break;
      case 'hierarchy':
        inp_type = 'checkbox';
        break;
    }

    let list_item = <a href="#">{term.name}</a>;

    if (term.branch && term.method != 'determinant') {
      list_item = (
        <span>
          <input type={inp_type} id={term.slug} checked={term.tagged}/>
          <label htmlFor={term.slug}>{term.name}</label>
        </span>
      )
    }

    let parent_idx = term.id;
    return (
      <li onClick={e => {
                          e.preventDefault()
                          e.stopPropagation()
                          actions.toggle(term)
                        }}>
        {list_item}
        <ul>
          {term.children.map(term =>
            <RubricatorItem key={term.id}
                            term={term}
                            actions={actions}
                            />
          )}
        </ul>
      </li>
    )
  }

}

