import React, { Component } from 'react';

export default class HowMany extends Component {
  render() {
    return (
      <div class="row">
        <div class="col-sm-6 ex-order-by ex-dropdown js-orderby-publication-app ex-state-closed">
          <ul class="ex-inline">
            <li><span>Сортировать по&nbsp;</span></li>
            <li>
              <div class="ex-sort-dropdown">
                <a href="#" class="ex-btn ex-btn-default ex-js-dropdown-toggle">
                  дате: сначала новые&nbsp;<span class="ex-icon-caret-down"></span>
                </a>
                <ul class="ex-dropdown-menu2">
                  <li>
                    <a href="#" class="ex-js-order-by" data-algorithm="date_added_asc">
                      дате: сначала старые
                    </a>
                  </li>
                  <li>
                    <a href="#" class="ex-js-order-by" data-algorithm="name_desc">
                      алфавиту по-убыванию
                    </a>
                  </li>
                  <li>
                    <a href="#" class="ex-js-order-by" data-algorithm="name_asc">
                      алфавиту
                    </a>
                  </li>
                </ul>
              </div>
            </li>
          </ul>
        </div>

        <div class="col-sm-3 ex-howmany-items ex-dropdown js-howmany-publication-app ex-state-closed">
          <ul class="ex-inline">
            <li>
              <span>Количество&nbsp;</span>&nbsp;
            </li>
            <li>
              <div class="ex-sort-dropdown">
                <a href="#" class="ex-btn ex-btn-default js-dropdown-toggle">
                  12&nbsp;<span class="ex-icon-caret-down"></span>
                </a>
                <ul class="ex-dropdown-menu2">
                  <li>
                    <a href="#" class="js-howmany" data-range="24">24</a>
                  </li>
                  <li>
                    <a href="#" class="js-howmany" data-range="60">60</a>
                  </li>
                  <li>
                    <a href="#" class="js-howmany" data-range="120">120</a>
                  </li>
                  <li>
                    <a href="#" class="js-howmany" data-range="240">240</a>
                  </li>
                </ul>
              </div>
            </li>
          </ul>
        </div>
      <div class="col-sm-3 ex-statistic js-statistic-publication-app">
        Элемент(ы) 1 - 12 из 3281
      </div>
    </div>
    );
  }
}
