$ ->
  socket = io.connect('http://' + document.domain + ':' + location.port)

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
