origPointOnMouseOver = Highcharts.Point::onMouseOver


Highcharts.Point::onMouseOver = (e) ->
  origPointOnMouseOver.call(this)
  chart = @series.chart
  tooltip = chart.tooltip
  if tooltip and tooltip.shared
    if chart.hoverPoints?
      tooltip.refresh(chart.hoverPoints, e)


zfill = (num, size) ->
  s = num + ''
  while s.length < size
    s = '0' + s
  return s


prepareChart = (numberOfPositions) ->
  $chart = $('#chart')
  $chart.highcharts 'StockChart',
    chart:
      type: 'area'
    title:
      text: null
    xAxis:
      tickmarkPlacement: 'on'
      title:
        enabled: false
      labels:
        enabled: false
    yAxis:
      title:
        text: 'Percent'
    legend:
      enabled: false
    navigator:
      enabled: false
    rangeSelector:
      enabled: false
    scrollbar:
      enabled: false
    tooltip:
      formatter: ->
        s = "<span style=\"font-size: 10px\">
               #{ Highcharts.dateFormat('%A, %b %e, %Y', @x) }
             </span>"
        points = _.sortBy(@points, (point) -> point.y)
        for point, index in points[-numberOfPositions..]
          strIndex = zfill(numberOfPositions - index, 2)
          if point.y > 0
            s += "<br/>#{ strIndex }
                  <span style=\"color: #{ point.series.color };\"> ● </span>"
            if point.series.state == 'hover'
              s += "<b>#{ point.series.name }</b>: <b>#{ point.y }</b>"
            else
              s += "#{ point.series.name }: <b>#{ point.y }</b>"
        return s
    plotOptions:
      area:
        stacking: 'percent'
        lineColor: '#ffffff'
        lineWidth: 1
        marker:
          enabled: false
      series:
        animation:
          complete: -> chart.reflow()
    series: []
  chart = $chart.highcharts()


sortObject = (obj, func, options) ->
  result = {}
  pairs = _.sortBy(_.pairs(obj), ([key, value]) -> func(key, value))
  if options?.reverse
    pairs = pairs.reverse()
  if options?.limit
    pairs = pairs[0 .. (options?.limit - 1)]
  for [key, value] in pairs
    result[key] = value
  return result


class PeriodicAccumalator
  constructor: (start, end, {timeframe}) ->
    @start = moment.utc(start * 1000)
    # @end = moment.utc(end * 1000).startOf('week').add(12, 'hours')
    @end = moment.utc(end * 1000)
    if timeframe != 'overall'
      @timeframe = (@end.unix() - @start.unix()) // 2
    else
      @timeframe = @end.unix() - @start.unix()
    @acc = {}

  add: (timestamp, item, count) ->
    @acc[timestamp] ?= {}
    @acc[timestamp][item] ?= 0
    @acc[timestamp][item] += count

  get: (timestamp) ->
    m = moment.utc(timestamp * 1000)
    start = moment.max(@start,
                       m.clone().subtract(@timeframe * 1000, 'milliseconds'))
    result = {}
    for timestamp, chart of @acc
      if start <= moment.utc(timestamp * 1000) <= m
        for item, count of chart
          result[item] ?= 0
          result[item] += count
    return result


drawChart = (charts, {timeframe, numberOfPositions}) ->
  weeklyCharts = {}
  acc = new PeriodicAccumalator(charts[0].toDate,
                                charts[charts.length - 1].toDate,
                                timeframe: timeframe)
  for {toDate, chart} in charts
    for item, count of chart ? {}
      acc.add(toDate, item, count)
    weeklyCharts[toDate] = acc.get(toDate)

  # Limit the number of artists per week
  totalItems = {}
  for timestamp, topitems of weeklyCharts
    weeklyCharts[timestamp] = sortObject(topitems, ((__, value) -> value),
                                         reverse: true,
                                         limit: numberOfPositions)
    for item, count of weeklyCharts[timestamp]
      totalItems[item] = count
  totalItems = sortObject(totalItems, (__, value) -> value)

  items = {}
  items[item] = {} for item of totalItems
  timestamps = []
  for timestamp, topitems of weeklyCharts
    timestamps.push(timestamp)
    for item, count of topitems
      items[item][timestamp] = count

  # Limit timeframe to last half.
  if timeframe != 'overall'
    timestamps = timestamps[-timestamps.length // 2 .. -1]

  chart = prepareChart(numberOfPositions)
  for item, weeks of items
    series =
      name: item
      data:
        ([timestamp * 1000, weeks[timestamp] ? 0] for timestamp in timestamps)
    chart.addSeries(series, false)
  chart.redraw()


navbarCollapsedState = (action) ->
  $settingsBlock = $('#settings-block')
  $settingsBlock[action + 'Class']('collapsed')
  $form = $('#form')
  if $settingsBlock.hasClass('collapsed')
    $form.css('pointer-events', 'none')
    $settingsBlock.css('left', -$settingsBlock.width() + 72)
  else
    $form.css('pointer-events', 'auto')
    $settingsBlock.css('left', 0)


hideAlert = ->
  $('#alert').addClass('hidden')
  $('#alert')
    .removeClass('alert-success')
    .removeClass('alert-info')
    .removeClass('alert-warning')
    .removeClass('alert-danger')


showAlert = (type, reason, message) ->
  $('#alert-reason').text(reason)
  $('#alert-message').text(message)
  $('#alert').addClass('alert-' + type).removeClass('hidden')


spanRange = (start, end, args...) ->
  result = []
  s = start.clone()
  while s < end
    e = moment.min(end, s.clone().add(1, 'week'))
    result.push([s.unix(), e.unix()])
    s.add(args...)
  return result


getJSON = (url, params) ->
  new Promise (resolve, reject) ->
    $.getJSON(url, params)
    .done (result) -> resolve(result)
    .fail (jqxhr, textStatus, reason) ->
      message = jqxhr.responseJSON?.error ? reason
      error = new Error(message)
      error.jqxhr = jqxhr
      error.textStatus = textStatus
      error.reason = reason
      reject(error)


setDefaults = (params) ->
  username = params['username']
  chartType = params['chart-type'] ? 'artist'
  numberOfPositions = params['number-of-positions'] ? '20'
  timeframe = params['timeframe'] ? 'last-3-months'
  $('#username').val(username)
  $('#chart-type').val(chartType)
  $('#number-of-positions').val(numberOfPositions)
  $('#timeframe').val(timeframe)
  return {username, chartType, numberOfPositions, timeframe}


submit = ->
  ladda = Ladda.create($('#submit')[0])
  ladda.start()
  hideAlert()

  state = History.getState()
  params = setDefaults(state.data)

  getJSON($SCRIPT_ROOT + '/info', {username: params.username})
  .then (info) ->
    $username = $('#username')
    $username.parent().removeClass('has-error').removeClass('has-feedback')
    $username.next('i.form-control-feedback').addClass('hidden')
    toDate = moment.utc()
    fromDate = switch params.timeframe
      when 'last-7-days'    then toDate.clone().subtract(2,  'week' )
      when 'last-month'     then toDate.clone().subtract(2,  'month')
      when 'last-3-months'  then toDate.clone().subtract(6,  'month')
      when 'last-6-months'  then toDate.clone().subtract(12, 'month')
      when 'last-12-months' then toDate.clone().subtract(24, 'month')
      when 'overall'        then moment.utc(info.registered * 1000)
    fromDate.startOf('week').add(12, 'hours')

    ranges = spanRange(fromDate, toDate, 1, 'week').reverse()
    progress = 0
    Promise.map ranges, ([fromDate, toDate]) ->
      getJSON(
        $SCRIPT_ROOT + '/weekly-chart',
        username: params.username,
        chartType: params.chartType,
        fromDate: fromDate,
        toDate: toDate)
      .then (response) ->
        if response.error?
          console.error(new Error(response.error))
        progress += 1
        ladda.setProgress(progress / ranges.length)
        response
      .catch (err) ->
        console.error(err)
        showAlert('danger', 'Server Error', 'Failed to get weekly charts.')
        ladda.stop()
  .then (charts) ->
    failedWeeksArray = []
    for {toDate, error} in charts
      if error?
        failedWeeksArray.push(
          moment.utc(toDate * 1000).format('MMM D, YYYY'))
    if failedWeeksArray.length > 0
      failedWeeks = failedWeeksArray.join(', ')
      showAlert('warning', 'Last.fm Error',
                "Weeks ending on #{ failedWeeks } failed to load.")

    drawChart(charts.reverse(), params)
    ladda.stop()
    unless failedWeeksArray.length > 0
      navbarCollapsedState('add')
  .catch (err) ->
    console.error(err)
    if err.message.indexOf('error code 6') > -1
      # No user with that name was found.
      $username = $('#username')
      $username.parent().addClass('has-error').addClass('has-feedback')
      $username.next('i.form-control-feedback').removeClass('hidden')
      showAlert('danger', 'Last.fm Error', 'No such user exists.')
    else
      showAlert('danger', 'Server Error', 'Failed to get weekly charts.')
    ladda.stop()


$ ->
  setDefaults($GET_PARAMS)

  $(window).resize ->
    $settingsBlock = $('#settings-block')
    if $settingsBlock.hasClass('collapsed')
      $settingsBlock.css('left', -$settingsBlock.width() + 72)

  $('#form').submit ->
    oldParams = History.getState().data
    params =
      'username': $('#username').val().trim()
      'chart-type': $('#chart-type option:selected').val()
      'number-of-positions': $('#number-of-positions option:selected').val()
      'timeframe': $('#timeframe option:selected').val()
    # If state didn't change, submit data anyway.
    if _.isEqual(params, oldParams)
      submit()
    else
      History.pushState(params, 'Elaborate Last.fm charts',
                        '?' + $.param(params))
    # Prevent form from being submitted
    return false

  History.Adapter.bind window, 'statechange', ->
    submit()

  $('#settings-block .navbar-toggle').click ->
    navbarCollapsedState('toggle')

  unless _.all(_.values($GET_PARAMS), _.isNull)
    $('#form').submit()

  $('.btn-xxs').popover
    html: true
    content: ->
      '<input type="text" class="form-control input-sm"
         value="' + History.getLocationHref() + '" onclick="this.select();" />'
    placement: 'top'
    title: 'Copy and share with friends'
    template: """
      <div class="popover" role="tooltip">
        <div class="arrow"></div>
        <button type="button" class="close"
            onclick="$('.btn-xxs').popover('hide');">
          <span aria-hidden="true">&times;&nbsp;</span>
          <span class="sr-only">Close</span>
        </button>
        <h3 class="popover-title"></h3>
        <div class="popover-content"></div>
      </div>
    """

  $('.btn-xxs').on 'shown.bs.popover', ->
    $('.popover input').focus().select()

  $(window).click (e) ->
    unless $(e.target).parents('.popover').length or
           $(e.target).is('.btn-xxs')
      $('.btn-xxs').popover('hide')
