var PeriodicAccumalator, drawChart, getJSON, hideAlert, navbarCollapsedState, origPointOnMouseOver, prepareChart, setDefaults, showAlert, sortObject, spanRange, submit, zfill;

origPointOnMouseOver = Highcharts.Point.prototype.onMouseOver;

Highcharts.Point.prototype.onMouseOver = function(e) {
  var chart, tooltip;
  origPointOnMouseOver.call(this);
  chart = this.series.chart;
  tooltip = chart.tooltip;
  if (tooltip && tooltip.shared) {
    if (chart.hoverPoints != null) {
      return tooltip.refresh(chart.hoverPoints, e);
    }
  }
};

zfill = function(num, size) {
  var s;
  s = num + '';
  while (s.length < size) {
    s = '0' + s;
  }
  return s;
};

prepareChart = function(numberOfPositions) {
  var $chart, chart;
  $chart = $('#chart');
  $chart.highcharts('StockChart', {
    chart: {
      type: 'area'
    },
    title: {
      text: null
    },
    xAxis: {
      tickmarkPlacement: 'on',
      title: {
        enabled: false
      },
      labels: {
        enabled: false
      }
    },
    yAxis: {
      title: {
        text: 'Percent'
      }
    },
    legend: {
      enabled: false
    },
    navigator: {
      enabled: false
    },
    rangeSelector: {
      enabled: false
    },
    scrollbar: {
      enabled: false
    },
    tooltip: {
      formatter: function() {
        var i, index, len, point, points, ref, s, strIndex;
        s = `<span style=\"font-size: 10px\"> ${Highcharts.dateFormat('%A, %b %e, %Y', this.x)} </span>`;
        points = _.sortBy(this.points, function(point) {
          return point.y;
        });
        ref = points.slice(-numberOfPositions);
        for (index = i = 0, len = ref.length; i < len; index = ++i) {
          point = ref[index];
          strIndex = zfill(numberOfPositions - index, 2);
          if (point.y > 0) {
            s += `<br/>${strIndex} <span style=\"color: ${point.series.color};\"> ● </span>`;
            if (point.series.state === 'hover') {
              s += `<b>${point.series.name}</b>: <b>${point.y}</b>`;
            } else {
              s += `${point.series.name}: <b>${point.y}</b>`;
            }
          }
        }
        return s;
      }
    },
    plotOptions: {
      area: {
        stacking: 'percent',
        lineColor: '#ffffff',
        lineWidth: 1,
        marker: {
          enabled: false
        }
      },
      series: {
        animation: {
          complete: function() {
            return chart.reflow();
          }
        }
      }
    },
    series: []
  });
  return chart = $chart.highcharts();
};

sortObject = function(obj, func, options) {
  var i, key, len, pairs, result, value;
  result = {};
  pairs = _.sortBy(_.pairs(obj), function([key, value]) {
    return func(key, value);
  });
  if (options != null ? options.reverse : void 0) {
    pairs = pairs.reverse();
  }
  if (options != null ? options.limit : void 0) {
    pairs = pairs.slice(0, +((options != null ? options.limit : void 0) - 1) + 1 || 9e9);
  }
  for (i = 0, len = pairs.length; i < len; i++) {
    [key, value] = pairs[i];
    result[key] = value;
  }
  return result;
};

PeriodicAccumalator = class PeriodicAccumalator {
  constructor(start, end, {timeframe}) {
    this.start = moment.utc(start * 1000);
    // @end = moment.utc(end * 1000).startOf('week').add(12, 'hours')
    this.end = moment.utc(end * 1000);
    if (timeframe !== 'overall') {
      this.timeframe = Math.floor((this.end.unix() - this.start.unix()) / 2);
    } else {
      this.timeframe = this.end.unix() - this.start.unix();
    }
    this.acc = {};
  }

  add(timestamp, item, count) {
    var base, base1;
    if ((base = this.acc)[timestamp] == null) {
      base[timestamp] = {};
    }
    if ((base1 = this.acc[timestamp])[item] == null) {
      base1[item] = 0;
    }
    return this.acc[timestamp][item] += count;
  }

  get(timestamp) {
    var chart, count, item, m, ref, ref1, result, start;
    m = moment.utc(timestamp * 1000);
    start = moment.max(this.start, m.clone().subtract(this.timeframe * 1000, 'milliseconds'));
    result = {};
    ref = this.acc;
    for (timestamp in ref) {
      chart = ref[timestamp];
      if ((start <= (ref1 = moment.utc(timestamp * 1000)) && ref1 <= m)) {
        for (item in chart) {
          count = chart[item];
          if (result[item] == null) {
            result[item] = 0;
          }
          result[item] += count;
        }
      }
    }
    return result;
  }

};

drawChart = function(charts, {timeframe, numberOfPositions}) {
  var acc, chart, count, i, item, items, len, ref, ref1, series, timestamp, timestamps, toDate, topitems, totalItems, weeklyCharts, weeks;
  weeklyCharts = {};
  acc = new PeriodicAccumalator(charts[0].toDate, charts[charts.length - 1].toDate, {
    timeframe: timeframe
  });
  for (i = 0, len = charts.length; i < len; i++) {
    ({toDate, chart} = charts[i]);
    ref = chart != null ? chart : {};
    for (item in ref) {
      count = ref[item];
      acc.add(toDate, item, count);
    }
    weeklyCharts[toDate] = acc.get(toDate);
  }
  // Limit the number of artists per week
  totalItems = {};
  for (timestamp in weeklyCharts) {
    topitems = weeklyCharts[timestamp];
    weeklyCharts[timestamp] = sortObject(topitems, (function(__, value) {
      return value;
    }), {
      reverse: true,
      limit: numberOfPositions
    });
    ref1 = weeklyCharts[timestamp];
    for (item in ref1) {
      count = ref1[item];
      totalItems[item] = count;
    }
  }
  totalItems = sortObject(totalItems, function(__, value) {
    return value;
  });
  items = {};
  for (item in totalItems) {
    items[item] = {};
  }
  timestamps = [];
  for (timestamp in weeklyCharts) {
    topitems = weeklyCharts[timestamp];
    timestamps.push(timestamp);
    for (item in topitems) {
      count = topitems[item];
      items[item][timestamp] = count;
    }
  }
  // Limit timeframe to last half.
  if (timeframe !== 'overall') {
    timestamps = timestamps.slice(Math.floor(-timestamps.length / 2));
  }
  chart = prepareChart(numberOfPositions);
  for (item in items) {
    weeks = items[item];
    series = {
      name: item,
      data: (function() {
        var j, len1, ref2, results;
        results = [];
        for (j = 0, len1 = timestamps.length; j < len1; j++) {
          timestamp = timestamps[j];
          results.push([timestamp * 1000, (ref2 = weeks[timestamp]) != null ? ref2 : 0]);
        }
        return results;
      })()
    };
    chart.addSeries(series, false);
  }
  return chart.redraw();
};

navbarCollapsedState = function(action) {
  var $form, $settingsBlock;
  $settingsBlock = $('#settings-block');
  $settingsBlock[action + 'Class']('collapsed');
  $form = $('#form');
  if ($settingsBlock.hasClass('collapsed')) {
    $form.css('pointer-events', 'none');
    return $settingsBlock.css('left', -$settingsBlock.width() + 72);
  } else {
    $form.css('pointer-events', 'auto');
    return $settingsBlock.css('left', 0);
  }
};

hideAlert = function() {
  $('#alert').addClass('hidden');
  return $('#alert').removeClass('alert-success').removeClass('alert-info').removeClass('alert-warning').removeClass('alert-danger');
};

showAlert = function(type, reason, message) {
  $('#alert-reason').text(reason);
  $('#alert-message').text(message);
  return $('#alert').addClass('alert-' + type).removeClass('hidden');
};

spanRange = function(start, end, ...args) {
  var e, result, s;
  result = [];
  s = start.clone();
  while (s < end) {
    e = moment.min(end, s.clone().add(1, 'week'));
    result.push([s.unix(), e.unix()]);
    s.add(...args);
  }
  return result;
};

getJSON = function(url, params) {
  return new Promise(function(resolve, reject) {
    return $.getJSON(url, params).done(function(result) {
      return resolve(result);
    }).fail(function(jqxhr, textStatus, reason) {
      var error, message, ref, ref1;
      message = (ref = (ref1 = jqxhr.responseJSON) != null ? ref1.error : void 0) != null ? ref : reason;
      error = new Error(message);
      error.jqxhr = jqxhr;
      error.textStatus = textStatus;
      error.reason = reason;
      return reject(error);
    });
  });
};

setDefaults = function(params) {
  var chartType, numberOfPositions, ref, ref1, ref2, timeframe, username;
  username = params['username'];
  chartType = (ref = params['chart-type']) != null ? ref : 'artist';
  numberOfPositions = (ref1 = params['number-of-positions']) != null ? ref1 : '20';
  timeframe = (ref2 = params['timeframe']) != null ? ref2 : 'last-3-months';
  $('#username').val(username);
  $('#chart-type').val(chartType);
  $('#number-of-positions').val(numberOfPositions);
  $('#timeframe').val(timeframe);
  return {username, chartType, numberOfPositions, timeframe};
};

submit = function() {
  var ladda, params, state;
  ladda = Ladda.create($('#submit')[0]);
  ladda.start();
  hideAlert();
  state = History.getState();
  params = setDefaults(state.data);
  return getJSON($SCRIPT_ROOT + '/info', {
    username: params.username
  }).then(function(info) {
    var $username, fromDate, progress, ranges, toDate;
    $username = $('#username');
    $username.parent().removeClass('has-error').removeClass('has-feedback');
    $username.next('i.form-control-feedback').addClass('hidden');
    toDate = moment.utc();
    fromDate = (function() {
      switch (params.timeframe) {
        case 'last-7-days':
          return toDate.clone().subtract(2, 'week');
        case 'last-month':
          return toDate.clone().subtract(2, 'month');
        case 'last-3-months':
          return toDate.clone().subtract(6, 'month');
        case 'last-6-months':
          return toDate.clone().subtract(12, 'month');
        case 'last-12-months':
          return toDate.clone().subtract(24, 'month');
        case 'overall':
          return moment.utc(info.registered * 1000);
      }
    })();
    fromDate.startOf('week').add(12, 'hours');
    ranges = spanRange(fromDate, toDate, 1, 'week').reverse();
    progress = 0;
    return Promise.map(ranges, function([fromDate, toDate]) {
      return getJSON($SCRIPT_ROOT + '/weekly-chart', {
        username: params.username,
        chartType: params.chartType,
        fromDate: fromDate,
        toDate: toDate
      }).then(function(response) {
        if (response.error != null) {
          console.error(new Error(response.error));
        }
        progress += 1;
        ladda.setProgress(progress / ranges.length);
        return response;
      }).catch(function(err) {
        console.error(err);
        showAlert('danger', 'Server Error', 'Failed to get weekly charts.');
        return ladda.stop();
      });
    });
  }).then(function(charts) {
    var error, failedWeeks, failedWeeksArray, i, len, toDate;
    failedWeeksArray = [];
    for (i = 0, len = charts.length; i < len; i++) {
      ({toDate, error} = charts[i]);
      if (error != null) {
        failedWeeksArray.push(moment.utc(toDate * 1000).format('MMM D, YYYY'));
      }
    }
    if (failedWeeksArray.length > 0) {
      failedWeeks = failedWeeksArray.join(', ');
      showAlert('warning', 'Last.fm Error', `Weeks ending on ${failedWeeks} failed to load.`);
    }
    drawChart(charts.reverse(), params);
    ladda.stop();
    if (!(failedWeeksArray.length > 0)) {
      return navbarCollapsedState('add');
    }
  }).catch(function(err) {
    var $username;
    console.error(err);
    if (err.message.indexOf('error code 6') > -1) {
      // No user with that name was found.
      $username = $('#username');
      $username.parent().addClass('has-error').addClass('has-feedback');
      $username.next('i.form-control-feedback').removeClass('hidden');
      showAlert('danger', 'Last.fm Error', 'No such user exists.');
    } else {
      showAlert('danger', 'Server Error', 'Failed to get weekly charts.');
    }
    return ladda.stop();
  });
};

$(function() {
  setDefaults($GET_PARAMS);
  $(window).resize(function() {
    var $settingsBlock;
    $settingsBlock = $('#settings-block');
    if ($settingsBlock.hasClass('collapsed')) {
      return $settingsBlock.css('left', -$settingsBlock.width() + 72);
    }
  });
  $('#form').submit(function() {
    var oldParams, params;
    oldParams = History.getState().data;
    params = {
      'username': $('#username').val().trim(),
      'chart-type': $('#chart-type option:selected').val(),
      'number-of-positions': $('#number-of-positions option:selected').val(),
      'timeframe': $('#timeframe option:selected').val()
    };
    // If state didn't change, submit data anyway.
    if (_.isEqual(params, oldParams)) {
      submit();
    } else {
      History.pushState(params, 'Elaborate Last.fm charts', '?' + $.param(params));
    }
    // Prevent form from being submitted
    return false;
  });
  History.Adapter.bind(window, 'statechange', function() {
    return submit();
  });
  $('#settings-block .navbar-toggle').click(function() {
    return navbarCollapsedState('toggle');
  });
  if (!_.all(_.values($GET_PARAMS), _.isNull)) {
    $('#form').submit();
  }
  $('.btn-xxs').popover({
    html: true,
    content: function() {
      return '<input type="text" class="form-control input-sm" value="' + History.getLocationHref() + '" onclick="this.select();" />';
    },
    placement: 'top',
    title: 'Copy and share with friends',
    template: `<div class="popover" role="tooltip">
  <div class="arrow"></div>
  <button type="button" class="close"
      onclick="$('.btn-xxs').popover('hide');">
    <span aria-hidden="true">&times;&nbsp;</span>
    <span class="sr-only">Close</span>
  </button>
  <h3 class="popover-title"></h3>
  <div class="popover-content"></div>
</div>`
  });
  $('.btn-xxs').on('shown.bs.popover', function() {
    return $('.popover input').focus().select();
  });
  return $(window).click(function(e) {
    if (!($(e.target).parents('.popover').length || $(e.target).is('.btn-xxs'))) {
      return $('.btn-xxs').popover('hide');
    }
  });
});
