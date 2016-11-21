import React, { Component } from 'react';
import _ from 'underscore';


export default class Paginator extends Component {

  handleNextClick(e) {
    e.preventDefault();
    e.stopPropagation();
    const { limit, offset, count, request_options } = this.props.meta;
    const actions = this.props.actions;
    let options = Object.assign(request_options, {'offset': offset + limit});
    this.props.actions.notifyLoading();
    this.props.actions.getEntities(options);
  }

  handlePrevClick(e) {
    e.preventDefault();
    e.stopPropagation();
    const { limit, offset, count, request_options } = this.props.meta;
    const actions = this.props.actions;
    let options = Object.assign(request_options, {'offset': offset - limit});
    this.props.actions.notifyLoading();
    this.props.actions.getEntities(options);
  }

  handlePageClick(e, n) {
    e.preventDefault();
    e.stopPropagation();
    const { limit, offset, count, request_options } = this.props.meta;
    const actions = this.props.actions;
    let options = Object.assign(request_options, {'offset': limit * (n - 1)});
    this.props.actions.notifyLoading();
    this.props.actions.getEntities(options);
  }

  render() {
    // Digg-style pagination settings
    const leadingPageRangeDisplayed = 8,
          trailingPageRangeDisplayed = 8,
          leadingPageRange = 6,
          trailingPageRange = 6,
          numPagesOutsideRange = 2,
          adjacentPages = 2;

    const { limit, offset, count } = this.props.meta;

    if (!(limit && count))
      return <div></div>;

    let inLeadingRange = false,
        inTrailingRange = false,
        pagesOutsideLeadingRange = _.range(0),
        pagesOutsideTrailingRange = _.range(0),
        currentPage = Math.floor(offset / limit) + 1,
        numPages = Math.ceil(count / limit),
        pageNumbers;

    if ( numPages <= leadingPageRangeDisplayed + numPagesOutsideRange + 1 ) {
      inLeadingRange = inTrailingRange = true;
      pageNumbers = _.filter(_.range(1, numPages + 1), function(n){
        return n > 0 && n <= numPages;
      });
    } else if ( currentPage <= leadingPageRange ) {
      inLeadingRange = true;
      pageNumbers = _.filter(_.range(1, leadingPageRangeDisplayed + 1), function(n){
        return n > 0 && n <= numPages;
      });
      pagesOutsideLeadingRange = _.map(_.range(0, -1 * numPagesOutsideRange, -1), function(n){
        return n + numPages;
      });
    } else if ( currentPage > numPages - trailingPageRange ) {
      inTrailingRange = true;
      pageNumbers = _.filter(_.range(numPages - trailingPageRangeDisplayed + 1, numPages + 1), function(n){
        return n > 0 && n <= numPages;
      });
      pagesOutsideTrailingRange = _.map(_.range(0, numPagesOutsideRange), function(n){
        return n + 1;
      });
    } else {
      pageNumbers = _.filter(_.range(currentPage - adjacentPages, currentPage + adjacentPages + 1), function(n){
        return n > 0 && n <= numPages;
      });
      pagesOutsideLeadingRange = _.map(_.range(0, -1 * numPagesOutsideRange, -1), function(n){
        return n + numPages;
      });
      pagesOutsideTrailingRange = _.map(_.range(0, numPagesOutsideRange), function(n){
        return n + 1;
      });
    }

    let hasNext = currentPage < numPages,
        hasPrevious = currentPage > 1;

    let previous = "";
    if (hasPrevious) {
      previous = (
        <li onClick={e => { ::this.handlePrevClick(e)}}>
          <a href="#"><i className="ex-icon-chevron-left"></i></a>
        </li>
      );
    } else {
      previous = (
        <li className="ex-disabled">
          <a href="#"><i className="ex-icon-chevron-left"></i></a>
        </li>
      );
    }

    let self = this;

    let pages = [];
    if ( !inLeadingRange ) {
      _.each(pagesOutsideTrailingRange, function(n) {
        pages.push(
          <li key={n} onClick={e => { ::self.handlePageClick(e, n)}}>
            <a href="#">{n}</a>
          </li>
        );
      });
      pages.push(
        <li><span className="ex-separator">…</span></li>
      );
    }

    _.each(pageNumbers, function(n) {
      if (currentPage == n) {
        pages.push(
          <li key={n} className="ex-active"><span>{n}</span></li>
        );
      } else {
        pages.push(
          <li onClick={e => { ::self.handlePageClick(e, n)}}>
            <a href="#">{n}</a>
          </li>
        );
      }
    });

    if ( !inTrailingRange ) {
      pages.push(
        <li><span className="ex-separator">…</span></li>
      );
      _.each(pagesOutsideLeadingRange.reverse(), function(n) {
        pages.push(
          <li key={n} onClick={e => { ::self.handlePageClick(e, n)}}>
            <a href="#">{n}</a>
          </li>
        );
      });
    }

    let next = "";
    if (hasNext) {
      next = (
        <li onClick={e => { ::this.handleNextClick(e)}}>
          <a href="#"><i className="ex-icon-chevron-right"></i></a>
        </li>
      );
    } else {
      next = (
        <li className="ex-disabled">
          <a href="#"><i className="ex-icon-chevron-right"></i></a>
        </li>
      );
    }

    let ret = (
      <div className="ex-catalog-pagination">
        <ul className="ex-pagination">
          {previous}
          {pages}
          {next}
        </ul>
      </div>
    );

    return ret;
  }
}

