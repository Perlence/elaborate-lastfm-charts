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
      categories: timestamps.map (ts) ->
        ts = moment.unix(ts)
        ts.format('YYYY-MM-DD') + '—' + ts.add(1, 'week').format('YYYY-MM-DD')
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
    if timestamp == 'errors'
      continue
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
    numberOfArtists = $('#number-of-artists option:selected').val()
    timeframe = $('#timeframe option:selected').val()
    cumulative = $('#cumulative').is(':checked')

    $.getJSON(
      $SCRIPT_ROOT + '/weekly-artist-charts'
      {username, numberOfArtists, timeframe, cumulative}
      drawChart)
