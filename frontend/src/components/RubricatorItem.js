import React, { Component, PropTypes } from 'react';

export default class RubricatorItem extends Component {
  static propTypes = {
    term: PropTypes.object.isRequired
  };

  render() {

    const { term, actions } = this.props;

    let inp_type = false;

    switch (term.method) {
      case 'facet': // Взять из константов
        inp_type = 'radio';
        break;
      case 'hierarchy':
        inp_type = 'checkbox';
        break;
    }
// В любом случаи за образец надо взять этот коде...
// https://github.com/Excentrics/publication-backbone/blob/master/publication_backbone/templates/publication_backbone/rubricator/partials/rubric.html

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
      <li onClick={e => { // Так делать не стоит, пусть будет в виде onClick={::this.handleClick}
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

