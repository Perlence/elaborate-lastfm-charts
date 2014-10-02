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


$ ->
  weeks = []
  artists = []
  data = {}

  socket = io.connect('http://' + document.domain + ':' + location.port)

  socket.on 'weeks', (_weeks) ->
    weeks = _weeks
    prepareChart(_weeks)

  socket.on 'week', (week) ->
    [timestamp, pairs] = week
    chart = $('#chart').highcharts()
    for [artist, count] in pairs
      if artist not in artists
        data[artist] = []
        artists.push(artist)
        data[artist] = (0 for __ in weeks)
        chart.addSeries
          name: artist
          data: data[artist]
        , false
      seriesIndex = artists.indexOf(artist)
      data[artist][weeks.indexOf(timestamp)] = count
      chart.series[seriesIndex].setData(data[artist], false)
    chart.redraw()

  $('#submit').click ->
    weeks = []
    artists = []
    data = {}
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
