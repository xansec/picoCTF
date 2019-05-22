renderScoreboardTeamScore = _.template($("#scoreboard-teamscore-template").remove().text())
renderScoreboardTabs = _.template($("#scoreboard-tabs-template").remove().text())
renderScoreboard = _.template($("#scoreboard-template").remove().text())
renderScorepage = _.template($("#scorepage-template").remove().text())


load_teamscore = ->
  apiCall "GET", "http://localhost:5000/api/v1/team"
  .success (data) ->
    $("#scoreboard-teamscore").html renderScoreboardTeamScore({
      teamscore: data.score
    })
  .error (jqXHR) ->
    apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

@reloadGraph = ->
  reload = ->
    $(".progression-graph").empty()
    active_tab = $("ul#scoreboard-tabs li.active").data()
    if active_tab != undefined
      active_gid = active_tab.gid
      window.drawTopTeamsProgressionGraph "#"+active_gid+"-progression", active_gid

  setTimeout reload, 100

load_scoreboard_page = (boardname, page, tid) ->
  apiCall "GET", "http://localhost:5000/api/v1/stats/scoreboard/page?board=" + boardname + "&page=" + page
    .success (data) ->
      $('#' + boardname + " tbody").html(
        renderScorepage({
          scorepage: data
          page:page
          tid: tid
        })
      )
    .error (jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}


load_scoreboard = ->
  apiCall "GET", "http://localhost:5000/api/v1/stats/scoreboard"
  .success (data) ->
    $("#scoreboard-tabs").html(renderScoreboardTabs({
      data: data,
      renderScoreboard: renderScoreboard
    })).promise().then( ->
      data = data;
      paginate = ((board) ->
        $('#' + board.name + '-pagination').bootstrapPaginator({
          totalPages: board.pages,
          bootstrapMajorVersion: 3,
          numberOfPages: 10,
          currentPage: board.start_page,
          onPageClicked: ((e, eOriginal, type, page) ->
            load_scoreboard_page(board.name, page, data.tid)
          )
        })
      )
      Object.keys(data).forEach( (e) ->
        if Array.isArray(data[e])
          data[e].forEach(paginate)
        else if typeof(data[e]) == 'object'
          paginate(data[e])
      )
    )
    reloadGraph()
  .error (jqXHR) ->
    apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

$ ->
  load_scoreboard()
  load_teamscore()
