prepareChart = (weeks) ->
  $('#chart').highcharts
    chart:
      type: 'area'
    title:
      text: ''
    xAxis:
      categories: weeks.map (ts) -> moment.unix(ts).format('YYYY-MM-DD')
      tickmarkPlacement: 'on'
      title:
        enabled: false
    yAxis:
      title:
        text: 'Percent'
    plotOptions:
      area:
        stacking: 'percent'
        lineColor: '#ffffff'
        lineWidth: 1
        marker:
          lineWidth: 1
          lineColor: '#ffffff'
    series: []


$ ->
  weeks = []
  artists = []

  socket = io.connect('http://' + document.domain + ':' + location.port)

  socket.on 'weeks', (_weeks) ->
    weeks = _weeks
    prepareChart(_weeks)

  socket.on 'week', (week) ->
    [timestamp, pairs] = week
    chart = $('#chart').highcharts()
    for [artist, count] in pairs
      if artist not in artists
        artists.push(artist)
        chart.addSeries
          name: artist
          data: (0 for __ in weeks)
        , false
      seriesIndex = artists.indexOf(artist)
      pointsIndex = weeks.indexOf(timestamp)
      chart.series[seriesIndex].points[pointsIndex].update(y: count, false)
    chart.redraw()

  $('#submit').click ->
    username = $('#username').val().trim()
    timeRange = $('#time-range li.active').attr('id')
    fromDate = switch timeRange
      when 'last-7-days'    then moment.utc().subtract(1, 'week')
      when 'last-month'     then moment.utc().subtract(1, 'month')
      when 'last-3-months'  then moment.utc().subtract(3, 'months')
      when 'last-6-months'  then moment.utc().subtract(6, 'months')
      when 'last-12-months' then moment.utc().subtract(12, 'months')
      when 'overall'        then null
    toDate = moment.utc()
    socket.emit('weekly artist charts', {username, fromDate, toDate})
