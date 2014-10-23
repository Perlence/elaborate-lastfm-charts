prepareChart = (timestamps) ->
  $chart = $('#chart')
  $chart.highcharts
    chart:
      type: 'area'
      zoomType: 'x'
      panning: true,
      panKey: 'shift'
    title:
      text: null
    xAxis:
      categories: timestamps.map (ts) -> moment.unix(ts).format('YYYY-MM-DD')
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


drawChart = (charts, numberOfPositions, cumulative) ->
  weeklyCharts = {}
  acc = {}
  for {toDate, chart} in charts
    weeklyCharts[toDate] = {}
    if cumulative
      for item, count of chart ? {}
        acc[item] ?= 0
        acc[item] += count
      for item, count of acc
        weeklyCharts[toDate][item] = count
    else
      weeklyCharts[toDate] = chart

  # Limit the number of artists per week
  totalItems = {}
  for timestamp, topitems of weeklyCharts
    weeklyCharts[timestamp] = sortObject(topitems, ((__, value) -> value),
                                         reverse: true,
                                         limit: numberOfPositions)
    for item, count of weeklyCharts[timestamp]
      totalItems[item] ?= 0
      if cumulative
        totalItems[item] = count
      else
        totalItems[item] += count
  totalItems = sortObject(totalItems, (__, value) -> value)

  items = {}
  items[item] = {} for item of totalItems
  timestamps = []
  for timestamp, topitems of weeklyCharts
    timestamps.push(timestamp)
    for item, count of topitems
      items[item][timestamp] = count

  chart = prepareChart(timestamps)
  for item, weeks of items
    series =
      name: item
      data: (weeks[timestamp] ? 0 for timestamp in timestamps)
    chart.addSeries(series, false)
  chart.redraw()


spanRange = (start, end, args...) ->
  result = []
  s = start.clone()
  while s < end
    e = moment(Math.min(end, s.clone().add(1, 'week')))
    result.push([s.unix(), e.unix()])
    s.add(args...)
  return result


getJSON = (url, params) ->
  new Promise (resolve, reject) ->
    $.getJSON(url, params)
    .done (result) -> resolve(result)
    .fail (jqxhr, textStatus, error) -> reject(error)


$ ->
  $('#submit').click ->
    ladda = Ladda.create(this)
    ladda.start()
    username = $('#username').val().trim()
    chartType = $('#chart-type option:selected').val()
    numberOfPositions = $('#number-of-positions option:selected').val()
    timeframe = $('#timeframe option:selected').val()
    cumulative = $('#cumulative').is(':checked')

    getJSON($SCRIPT_ROOT + '/info', {username})
    .then (info) ->
      toDate = moment.utc()
      fromDate = switch timeframe
        when 'last-7-days'    then toDate.clone().subtract(1,  'week' )
        when 'last-month'     then toDate.clone().subtract(1,  'month')
        when 'last-3-months'  then toDate.clone().subtract(3,  'month')
        when 'last-6-months'  then toDate.clone().subtract(6,  'month')
        when 'last-12-months' then toDate.clone().subtract(12, 'month')
        when 'overall'        then moment.utc(info.registered * 1000)
      fromDate.startOf('week').add(12, 'hours')

      ranges = spanRange(fromDate, toDate, 1, 'week').reverse()
      progress = 0
      Promise.map ranges, ([fromDate, toDate]) ->
        params = {username, chartType, fromDate, toDate}
        getJSON($SCRIPT_ROOT + '/weekly-chart', params)
        .then (response) ->
          progress += 1
          ladda.setProgress(progress / ranges.length)
          # if response.error?
          #   # Put error handling here
          response
        .catch ->
          # Failed to get weekly charts.
          ladda.stop()
    .then (charts) ->
      drawChart(charts.reverse(), numberOfPositions, cumulative)
      ladda.stop()
      $('#settings-block').addClass('collapsed')
    .catch ->
      # Failed to get user info or there were server-side errors while getting
      # weekly charts.
      ladda.stop()

  $('#settings-block .navbar-toggle').click ->
    $('#settings-block').toggleClass('collapsed')
