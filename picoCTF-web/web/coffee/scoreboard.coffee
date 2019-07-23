renderScoreboardTeamScore = _.template($("#scoreboard-teamscore-template").remove().text())
renderScoreboardTabs = _.template($("#scoreboard-tabs-template").remove().text())
renderScoreboard = _.template($("#scoreboard-template").remove().text())
renderScorepage = _.template($("#scorepage-template").remove().text())


load_teamscore = ->
  apiCall "GET", "/api/v1/team"
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

load_scoreboard_page = (boardname, page, tid, gid="") ->
  if !gid
    targetid = boardname
  else
    boardname = "groups"
    targetid = gid
  apiCall "GET", "/api/v1/stats/scoreboard/page?board=" + boardname + "&page=" + page + "&gid=" + gid
    .success (data) ->
      $('#' + targetid + " tbody").html(
        renderScorepage({
          scorepage: data.scoreboard
          page: page
          tid: tid
        })
      )
    .error (jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}


load_scoreboard = ->
  apiCall "GET", "/api/v1/stats/scoreboard"
  .success (data) ->
    $("#scoreboard-tabs").html(renderScoreboardTabs({
      data: data,
      renderScoreboard: renderScoreboard
    })).promise().then( ->
      tid = data.tid
      paginate = ((board) ->
        $('#' + board.name + '-pagination').bootstrapPaginator({
          totalPages: board.pages,
          bootstrapMajorVersion: 3,
          numberOfPages: 10,
          currentPage: board.start_page,
          onPageClicked: ((e, eOriginal, type, page) ->
            load_scoreboard_page(board.name, page, data.tid, board.gid)
          )
        })
      )
      Object.keys(data).forEach( (e) ->
        if Array.isArray(data[e])
          data[e].forEach(paginate)
        else if typeof(data[e]) == 'object'
          paginate(data[e])
      )
      timeoutID_global = null;
      timeoutID_student = null;
      paginateSearch = ((pattern, board) ->
        $('#' + board.name + '-pagination').bootstrapPaginator({
          totalPages: Math.max(board.pages, 1),
          bootstrapMajorVersion: 3,
          numberOfPages: 10,
          currentPage: board.start_page,
          onPageClicked: ((e, eOriginal, type, page) ->
            searchBoard(pattern, board.name, page)
          )
        })
      )
      searchBoard = (pattern, board, page=0) ->
         if page == 0
           repaginate = true
           page = 1
         apiCall "GET", "/api/v1/stats/scoreboard/search?pattern=" + pattern + "&board=" + board + "&page=" + page
          .success (searchdata) ->
            $('#' + board + " tbody").html(
              renderScorepage({
                scorepage: searchdata.scoreboard
                page: page
                tid: tid
              })
             )
            if repaginate
              paginateSearch(pattern, searchdata)
      $('#global-search').keyup((e) ->
        if e.target.value.length > 2
          clearTimeout(timeoutID_global);
          timeoutID_global = setTimeout((() -> searchBoard(e.target.value, "global")), 250);
        else if e.target.value == ""
          load_scoreboard()
          reloadGraph()
      )
      $('#student-search').keyup((e) ->
        if e.target.value.length > 2
          clearTimeout(timeoutID_student);
          timeoutID_student = setTimeout((() -> searchBoard(e.target.value, "student")), 250);
        else if e.target.value == ""
          load_scoreboard().promise().then( ->
            $('#scoreboard-tabs a[href="#student"]').tab('show')
            reloadGraph()
          )
      )
    )
    reloadGraph()
  .error (jqXHR) ->
    apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

$ ->
  load_scoreboard()
  load_teamscore()
