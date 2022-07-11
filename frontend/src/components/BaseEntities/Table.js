import React, { Component } from 'react';
import TableItemMixin from 'components/BaseEntities/TableItemMixin';


// Container
export default class Table extends Component {
    render_table_headers(table_titles) {
        return (
            <thead>
            <tr>
              {Object.entries(table_titles).map(
                  ([key_name, field], i)=>
                      <th key={i}>{field}</th>)}
              </tr>
            </thead>);
    }

    render() {
        const { items, actions, loading, descriptions, meta } = this.props;

        const table_titles = this.render_table_headers(meta.extra.table_titles);

        return(
            <div className="ex-base-table">
              <table className='table'>
                  {table_titles}
                  <tbody>
                    {items.map(
                      (child, i) =>
                      <TableItem
                          key={i}
                          data={child}
                          actions={actions}
                          loading={loading}
                          descriptions={descriptions}
                          position={i}
                          meta={meta}
                      />)}
                  </tbody>
              </table>
            </div>);
    }
}

class TableItem extends TableItemMixin(Component) {

    render() {
        const { data, position, meta, descriptions } = this.props;

         let marks = data.short_marks || [];

         if (descriptions[data.id]) {
          marks = descriptions[data.id].marks || [];
        }

        const descriptionBaloon = this.getDescriptionBaloon(data, marks) || "",
            itemContent = this.getItemContent(data, meta.extra.table_titles, descriptionBaloon),
            itemBlock = this.getItemBlock(itemContent);

            return (
                <>{itemBlock}</>
            );
        };
}