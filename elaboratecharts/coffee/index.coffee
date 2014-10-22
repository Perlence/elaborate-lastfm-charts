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
        ts.format('YYYY-MM-DD') +
          '—' +
          ts.subtract(1, 'week').format('YYYY-MM-DD')
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


drawChart = (weeklyCharts, numberOfArtists, cumulative) ->
  if cumulative
    artistsAcc = {}
    for timestamp, topitems of weeklyCharts
      for artist, count of topitems
        artistsAcc[artist] ?= 0
        artistsAcc[artist] += count
      for artist, count of artistsAcc
        topitems[artist] = count

  # Limit the number of artists per week
  artistsTotal = {}
  for timestamp, topitems of weeklyCharts
    weeklyCharts[timestamp] = sortObject(topitems, ((__, value) -> value),
                                         reverse: true, limit: numberOfArtists)
    for artist, count of weeklyCharts[timestamp]
      artistsTotal[artist] ?= 0
      if cumulative
        artistsTotal[artist] = count
      else
        artistsTotal[artist] += count
  artistsTotal = sortObject(artistsTotal, (__, value) -> value)

  artists = {}
  artists[artist] = {} for artist of artistsTotal
  timestamps = []
  for timestamp, topitems of weeklyCharts
    timestamps.push(timestamp)
    for artist, count of topitems
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
    numberOfArtists = $('#number-of-artists option:selected').val()
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
      Promise.map ranges, (range) ->
        [fromDate, toDate] = range
        params = {username, fromDate, toDate}
        getJSON($SCRIPT_ROOT + '/weekly-artist-charts', params)
        .then (weeklyCharts) ->
          progress += 1
          ladda.setProgress(progress / ranges.length)
          # if weeklyCharts.error?
          #   # Put error handling here
          weeklyCharts
        .catch ->
          # Failed to get weekly charts.
          ladda.stop()
    .then (weeks) ->
      weeklyCharts = {}
      for week in weeks.reverse()
        for key, value of week
          if key != 'error'
            weeklyCharts[key] = value
      drawChart(weeklyCharts, numberOfArtists, cumulative)
      ladda.stop()
    .catch ->
      # Failed to get user info or there were server-side errors while getting
      # weekly charts.
      ladda.stop()
