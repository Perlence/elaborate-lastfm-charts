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
          lineWidth: 1
          lineColor: '#ffffff'
    series: []
  chart = $chart.highcharts()


drawChart = (weeklyCharts) ->
  artists = {}
  timestamps = []
  for timestamp, topitems of weeklyCharts
    timestamps.push(timestamp)
    for artist, count of topitems
      artists[artist] ?= {}
      artists[artist][timestamp] = count

  chart = prepareChart(timestamps)
  for artist, weeks of artists
    series =
      name: artist
      data: (weeks[timestamp] ? 0 for timestamp in timestamps)
    chart.addSeries(series, false)
  chart.redraw()


$ ->
  $('#submit').click ->
    username = $('#username').val().trim()
    timeRange = $('#time-range option:selected').attr('value')
    cumulative = $('#cumulative').is(':checked')
    toDate = moment.utc()
    fromDate = switch timeRange
      when 'last-7-days'    then toDate.clone().subtract(1,  'week' )
      when 'last-month'     then toDate.clone().subtract(1,  'month')
      when 'last-3-months'  then toDate.clone().subtract(3,  'month')
      when 'last-6-months'  then toDate.clone().subtract(6,  'month')
      when 'last-12-months' then toDate.clone().subtract(12, 'month')
      when 'overall'        then null

    fromDate = fromDate?.unix()
    toDate = toDate.unix()

    $.getJSON(
      $SCRIPT_ROOT + '/weekly-artist-charts'
      {username, fromDate, toDate, cumulative}
      drawChart)
