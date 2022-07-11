import React from 'react';
import marked from 'marked';
import ReactDOM from 'react-dom';

const TableItemMixin = Base => class extends Base{
    constructor() {
        super();
        this.state = {
            isHaveDescription: false,
            isHaveMarks: false,
            isHover: false,
            v_pos: null,
        };
    }

  handleMouseOver(e) {
        this.componentDidMount();
        setTimeout(() => {
            this.state.isHover = true;
            this.toggleDescription(e);
        },  10);
  }

  handleMouseOut(e) {
        setTimeout(() => {
            this.state.isHover = false;
            this.toggleDescription(e);
        }, 10);
  }

  toggleDescription(e) {
    const {data, actions, descriptions} = this.props,
      id = data.id;
    if (this.state.isHover) {
      actions.showDescription(id);
      if (!descriptions[id])
        actions.getEntityInfo(data);
    } else
      actions.hideDescription(id);
  }

  componentDidMount(x, y, z){
    const area = ReactDOM.findDOMNode(this),
          info = area.getElementsByClassName('ex-catalog-item-block')[0];

    if (info) {
      // HACK: для правильного определения размера в хроме функция вызывается с таймаутом
        const infoRect = info.getBoundingClientRect(),
            baloon = area.getElementsByClassName('ex-baloon')[0],
            window_height = window.innerHeight;
        setTimeout(() => {
        //Добавляю display: block для корректного получения высоты descriptionBaloon
        baloon.style.display = 'block';

        const baloonInfo = baloon.getBoundingClientRect();

        const height = baloonInfo.height,
              bottom = infoRect.bottom,
              v_pos = window_height < bottom + height ? 'bottom' : 'top';

        baloon.removeAttribute('style');

        this.setState({v_pos});
      }, 10);
    }
  }

  getDescriptionBaloon(data, marks) {
    if (marks.length) {
        this.state.isHaveDescription = true;

        return (
            <div className="ex-description-wrapper">
              <div className="ex-baloon">
                {this.state.v_pos === 'top' &&
                <div className="ex-baloon-arrow">
                    <div className="ex-arrow"/>
                </div>
                }
                <ul className="ex-baloon-ribbons">
                  {marks.map(
                    (child, i) =>
                      <li className="ex-baloon-ribbon"
                          key={i}
                          data-name={child.name}
                          data-path={child.path}
                          data-view-class={child.view_class.join(' ')}>
                        <div className="ex-baloon-ribbon">{child.values.join(', ')}</div>
                      </li>
                  )}
                </ul>
                {this.state.v_pos === 'bottom' &&
                <div className="ex-baloon-arrow">
                    <div className="ex-arrow"/>
                </div>
                }
              </div>
            </div>
            );
    }
  }
    renderTitle(data) {
        const title = data.entity_name;
        const url = data.extra?.url || data.entity_url;

        return (
            <td className="table-element">
                <a href={url} title={title}>
                    {title}
                </a>
            </td>);
    }

    renderMedia(data) {
        return (
            <td className="table-image table-element" dangerouslySetInnerHTML={{__html: marked(data.media, {sanitize: false})}}></td>);
    }

   renderEllipsis(descriptionBalloon) {
        return (this.state.isHaveDescription ?
                <td className={`table-element`}>
                    <div className={`ex-catalog-item ${this.state.isHover ? "ex-state-description" : ''}`}>
                    <i className={`fa fa-ellipsis-h fa-lg  more-info ex-catalog-item-block`}
                       aria-hidden="true"
                    onMouseOver={e => {
                        ::this.handleMouseOver(e)
                    }}
                    onMouseOut={e => {
                        ::this.handleMouseOut(e)
                    }}>
                        {descriptionBalloon}
                    </i>
                        </div>
                </td>
                :
                <td className="table-element">
                    <i className="fa fa-ellipsis-h fa-lg more-info disabled" aria-hidden="true"/>
                </td>);
    }


    renderDefault() {
        return (
            <td className="table-element">&nbsp;</td>);
    }

    getRenderFields() {
        return {
            'entity_name': this.renderTitle.bind(this),
            'media': this.renderMedia.bind(this),
            'default': this.renderDefault.bind(this),
            'short_marks': this.renderEllipsis.bind(this)
        }
    }

    getItemContent(data, tableFields, descriptionBaloon) {
        var content = [];
        const fieldRenders = this.getRenderFields();
        const copiedTableFields = {...tableFields};

        if (Object.keys(tableFields).includes('short_marks')
            && 'short_marks' in fieldRenders) {
            this.state.isHaveMarks = true;
            delete copiedTableFields['short_marks'];
        }

        Object.keys(copiedTableFields).forEach (
             (key)=> {
                 { key in fieldRenders ?
                     content.push(fieldRenders[key](data))
                     :
                     content.push(fieldRenders['default']())}
            });

        if (this.state.isHaveMarks)
            content.push(this.renderEllipsis(descriptionBaloon))

        return content;
    }

    getItemBlock(itemContent) {
        return (
            <tr className={`table-item table-row ex-catalog-item `}
                data-vertical-position={this.state.v_pos}>
                {itemContent}
            </tr>
        );
    }
};

export default TableItemMixin;