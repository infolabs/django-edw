import React, { Component } from 'react';
import Dropdown from './Dropdown';

export default class HowMany extends Component {
  render() {
    let sort_selected = "дате: сначала новыe",
        sort_options = ["дате: сначала старые", "алфавиту по-убыванию", "алфавиту"],
        quantity_selected = "12",
        quantity_options = ["24", "60", "120"];
    return (
      <div className="row">
        <div className="col-sm-6 ex-order-by ex-dropdown js-orderby-publication-app ex-state-closed">
          <ul className="ex-inline">
            <li><span>Сортировать по&nbsp;</span></li>
            <li>
              <Dropdown selected={sort_selected} options={sort_options}/>
            </li>
          </ul>
        </div>

        <div className="col-sm-3 ex-howmany-items ex-dropdown js-howmany-publication-app ex-state-closed">
          <ul className="ex-inline">
            <li>
              <span>Количество&nbsp;</span>&nbsp;
            </li>
            <li>
              <Dropdown selected={quantity_selected} options={quantity_options}/>
            </li>
          </ul>
        </div>
      <div className="col-sm-3 ex-statistic js-statistic-publication-app">
        Элемент(ы) 1 - 12 из 3281
      </div>
    </div>
    );
  }
}
