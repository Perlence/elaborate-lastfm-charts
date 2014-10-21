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
          enabled: false
      series:
        animation:
          complete: -> $(window).resize()
    series: []
  chart = $chart.highcharts()


drawChart = (weeklyCharts, numberOfArtists, cumulative) ->
  if cumulative
    artistsAcc = {}
    for timestamp, topitems of weeklyCharts
      for artist, count of topitems
        artistsAcc[artist] = (artistsAcc[artist] ? 0) + count
      for artist, count of artistsAcc
        if artist not in topitems
          topitems[artist] = count

  # Limit the number of artists
  for timestamp, topitems of weeklyCharts
    topitems = _.sortBy(_.pairs(topitems), ([key, value]) -> value)
    weeklyCharts[timestamp] = {}
    for [key, value] in topitems.reverse()[0..9]
      weeklyCharts[timestamp][key] = value

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


spanRange = (start, end, args...) ->
  result = []
  s = start.clone()
  while s < end
    e = moment(Math.min(end, s.clone().add(1, 'week')))
    result.push([s.unix(), e.unix()])
    s.add(args...)
  return result


$ ->
  $('#submit').click ->
    l = Ladda.create(this)
    l.start()
    username = $('#username').val().trim()
    numberOfArtists = $('#number-of-artists option:selected').val()
    timeframe = $('#timeframe option:selected').val()
    cumulative = $('#cumulative').is(':checked')

    toDate = moment.utc()
    fromDate = switch timeframe
      when 'last-7-days'    then toDate.clone().subtract(1,  'week' )
      when 'last-month'     then toDate.clone().subtract(1,  'month')
      when 'last-3-months'  then toDate.clone().subtract(3,  'month')
      when 'last-6-months'  then toDate.clone().subtract(6,  'month')
      when 'last-12-months' then toDate.clone().subtract(12, 'month')
      when 'overall'        then moment.utc(1108296002000)  # the earliest date
    fromDate.startOf('week').add(12, 'hours')

    Promise.map spanRange(fromDate, toDate, 1, 'week'), ([fromDate, toDate]) ->
      params = {username, fromDate, toDate}
      $.getJSON($SCRIPT_ROOT + '/weekly-artist-charts', params)
      .then (weeklyCharts) ->
        # Put progress bar here
        # if weeklyCharts.error?
        #   # Put error handling here
        weeklyCharts
    .then (weeks) ->
      weeklyCharts = {}
      for week in weeks
        for key, value of week
          if key != 'error'
            weeklyCharts[key] = value
      drawChart(weeklyCharts, numberOfArtists, cumulative)
      l.stop()
      $('.collapse').collapse()
