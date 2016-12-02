import React, { Component } from 'react';


export default class Paginator extends Component {

  handleNextClick(e) {
    e.preventDefault();
    e.stopPropagation();
    const { limit, offset, count, request_options } = this.props.meta;
    const actions = this.props.actions;
    let options = Object.assign(request_options, {'offset': offset + limit});
    this.props.actions.notifyLoadingEntities();
    this.props.actions.getEntities(this.props.mart_id, options);
  }

  handlePrevClick(e) {
    e.preventDefault();
    e.stopPropagation();
    const { limit, offset, count, request_options } = this.props.meta;
    const actions = this.props.actions;
    let options = Object.assign(request_options, {'offset': offset - limit});
    this.props.actions.notifyLoadingEntities();
    this.props.actions.getEntities(this.props.mart_id, options);
  }

  handlePageClick(e, n) {
    e.preventDefault();
    e.stopPropagation();
    const { limit, offset, count, request_options } = this.props.meta;
    const actions = this.props.actions;
    let options = Object.assign(request_options, {'offset': limit * (n - 1)});
    this.props.actions.notifyLoadingEntities();
    this.props.actions.getEntities(this.props.mart_id, options);
  }

  render() {

    let range = function(start = 0, stop, step = 1) {
      let ret = []
      let cur = (stop === undefined) ? 0 : start;
      let max = (stop === undefined) ? start : stop;
      for (let i = cur; step < 0 ? i > max : i < max; i += step)
        ret.push(i);
      return ret;
    }

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
        pagesOutsideLeadingRange = range(0),
        pagesOutsideTrailingRange = range(0),
        currentPage = Math.floor(offset / limit) + 1,
        numPages = Math.ceil(count / limit),
        pageNumbers;

    if ( numPages <= leadingPageRangeDisplayed + numPagesOutsideRange + 1 ) {
      inLeadingRange = inTrailingRange = true;
      pageNumbers = range(1, numPages + 1).filter(
        n => n > 0 && n <= numPages
      );
    } else if ( currentPage <= leadingPageRange ) {
      inLeadingRange = true;
      pageNumbers = range(1, leadingPageRangeDisplayed + 1).filter(
        n => n > 0 && n <= numPages
      );
      pagesOutsideLeadingRange = range(0, -1 * numPagesOutsideRange, -1).map(
        n => n + numPages
      );
    } else if ( currentPage > numPages - trailingPageRange ) {
      inTrailingRange = true;
      pageNumbers = range(numPages - trailingPageRangeDisplayed + 1, numPages + 1).filter(
        n => n > 0 && n <= numPages
      );
      pagesOutsideTrailingRange = range(0, numPagesOutsideRange).map(
        n => n + 1
      );
    } else {
      pageNumbers = range(currentPage - adjacentPages, currentPage + adjacentPages + 1).filter(
        n => n > 0 && n <= numPages
      );
      pagesOutsideLeadingRange = range(0, -1 * numPagesOutsideRange, -1).map(
        n => n + numPages
      );
      pagesOutsideTrailingRange = range(0, numPagesOutsideRange).map(
        n => n + 1
      );
    }

    let hasNext = currentPage < numPages,
        hasPrevious = currentPage > 1;

    let previous = "";
    if (hasPrevious) {
      previous = (
        <li key='prev' onClick={e => { ::this.handlePrevClick(e)}}>
          <a href="#"><i className="ex-icon-chevron-left"></i></a>
        </li>
      );
    } else {
      previous = (
        <li key='prev' className="ex-disabled">
          <a href="#"><i className="ex-icon-chevron-left"></i></a>
        </li>
      );
    }

    let self = this;

    let pages = [];
    if ( !inLeadingRange ) {
      pagesOutsideTrailingRange.forEach(function(n) {
        pages.push(
          <li key={n} onClick={e => { ::self.handlePageClick(e, n)}}>
            <a href="#">{n}</a>
          </li>
        );
      });
      pages.push(
        <li key='lead-sep'><span className="ex-separator">…</span></li>
      );
    }

    pageNumbers.forEach(function(n) {
      if (currentPage == n) {
        pages.push(
          <li key={n} className="ex-active"><span>{n}</span></li>
        );
      } else {
        pages.push(
          <li key={n} onClick={e => { ::self.handlePageClick(e, n)}}>
            <a href="#">{n}</a>
          </li>
        );
      }
    });

    if ( !inTrailingRange ) {
      pages.push(
        <li key='trail-sep'><span className="ex-separator">…</span></li>
      );
      pagesOutsideLeadingRange.reverse().forEach(function(n) {
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
        <li key='next' onClick={e => { ::this.handleNextClick(e)}}>
          <a href="#"><i className="ex-icon-chevron-right"></i></a>
        </li>
      );
    } else {
      next = (
        <li key='next' className="ex-disabled">
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

