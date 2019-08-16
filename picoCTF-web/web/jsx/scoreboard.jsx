const renderScoreboardTeamScore = _.template(
  $("#scoreboard-teamscore-template")
    .remove()
    .text()
);
const renderScoreboard = _.template(
  $("#scoreboard-template")
    .remove()
    .text()
);
const renderScoreboardPage = _.template(
  $("#scoreboard-page-template")
    .remove()
    .text()
);

window.reloadGraph = function() {
  const reload = function() {
    $(".progression-graph").empty();
    const active_tab = $("ul#scoreboard-tabs li.active").data();
    if (active_tab.sid !== undefined) {
      window.drawTopTeamsProgressionGraph(
        `#${active_tab.sid}-progression`,
        {'scoreboard_id': active_tab.sid}
      );
    }
    else if (active_tab.gid !== undefined) {
      window.drawTopTeamsProgressionGraph(
        `#${active_tab.gid}-progression`,
        {'group_id': active_tab.gid}
      );
    }
  };
  setTimeout(reload, 100);
};

const render_scoreboard = function(board_key, search) {
  // Re-render the scoreboard display, including the paginator

  // Build the scoreboard page endpoint URL
  var scoreboard_endpoint = '/api/v1/'
  if (board_key.hasOwnProperty('group_id')) {
    scoreboard_endpoint += 'groups/' + board_key.group_id + '/scoreboard';
  } else {
    scoreboard_endpoint += 'scoreboards/' + board_key.scoreboard_id + '/scoreboard';
  }
  if (search !== undefined) {
    scoreboard_endpoint += '?search=' + search
  }

  // If non-group scoreboard, get scoreboard metadata
  if (board_key.hasOwnProperty('scoreboard_id')) {
    var scoreboard_metadata_endpoint = '/api/v1/scoreboards/' + board_key.scoreboard_id;
  } else {
    var scoreboard_metadata_endpoint = null
  }

  // Fetch the scoreboard page and re-render the scoreboard display
  $.when(
    apiCall("GET", "/api/v1/team"),
    apiCall("GET", scoreboard_endpoint),
    (function() {
      if (scoreboard_metadata_endpoint !== null) {
        return apiCall("GET", scoreboard_metadata_endpoint)
      } else {
        return null
      }
    })()
  )
  .done(function(team_data, scoreboard_data, scoreboard_metadata) {
    var scoreboard_properties = {
      scorepage: scoreboard_data[0].scoreboard,
      current_page: scoreboard_data[0].current_page,
      total_pages: scoreboard_data[0].total_pages,
      scoreboard_name: null,
      scoreboard_sponsor: null,
      scoreboard_logo: null,
      user_tid: team_data[0].tid
    }
    if (scoreboard_metadata !== null) {
      scoreboard_properties = Object.assign(scoreboard_properties, {
        scoreboard_name: scoreboard_metadata[0].name,
        scoreboard_sponsor: scoreboard_metadata[0].sponsor,
        scoreboard_logo: scoreboard_metadata[0].logo
      })
    }
    var scoreboardContent = renderScoreboard(scoreboard_properties)
    $("#scoreboard-container").html(scoreboardContent).promise().then(
      function(){
        // Once content has loaded, set up paginator
        $("#pagination").bootstrapPaginator({
          totalPages: scoreboard_data[0].total_pages,
          bootstrapMajorVersion: 3,
          numberOfPages: 10,
          currentPage: scoreboard_data[0].current_page,
          onPageClicked(e, eOriginal, type, page) {
            render_scoreboard_page(board_key, "", page);
          }
        });
      }
    )
  })
  .fail(jqXHR =>
    apiNotify({ status: 0, message: jqXHR.responseJSON.message })
  );
};

const render_scoreboard_page = function(board_key, search, page) {
  // Re-render only the scoreboard page, keeping search field and pagination
  var searchValue = $("#search").val()

  // Build the scoreboard page endpoint URL
  var scoreboard_endpoint = '/api/v1/'
  if (board_key.hasOwnProperty('group_id')) {
    scoreboard_endpoint += 'groups/' + board_key.group_id + '/scoreboard';
  } else {
    scoreboard_endpoint += 'scoreboards/' + board_key.scoreboard_id + '/scoreboard';
  }
  scoreboard_endpoint += '?page=' + page
  if (search != "") {
    scoreboard_endpoint += '&search=' + searchValue
  }

  // Fetch the scoreboard page and re-render the scoreboard display
  $.when(
    apiCall("GET", "/api/v1/team"),
    apiCall("GET", scoreboard_endpoint)
  )
  .done(function(team_data, scoreboard_data) {
      var scoreboardPageContent = renderScoreboardPage({
        scorepage: scoreboard_data[0].scoreboard,
        current_page: scoreboard_data[0].current_page,
        user_tid: team_data[0].tid
      })
      $("#scoreboard-container tbody").html(scoreboardPageContent)
    })
  .fail(jqXHR =>
    apiNotify({ status: 0, message: jqXHR.responseJSON.message })
  );
};

const render_scoreboard_navigation = () =>
  $.when(
    apiCall("GET", "/api/v1/scoreboards"),
    apiCall("GET", "/api/v1/team"),
    apiCall("GET", "/api/v1/groups")
  ).done(function(scoreboard_data, team_data, group_data) {

    // Update the team score
    $("#scoreboard-teamscore").html(
      renderScoreboardTeamScore({
        teamscore: team_data[0].score
      })
    )

    // Create the eligible scoreboard and group tabs
    var eligibleScoreboards = scoreboard_data[0].filter((scoreboard) =>
      team_data[0].eligibilities.indexOf(scoreboard.sid) != -1)
    eligibleScoreboards = _.sortBy(eligibleScoreboards, 'name')
    eligibleScoreboards = _.sortBy(eligibleScoreboards, function(scoreboard) {
      // Sort by descending priority order
      return -(scoreboard['priority']);
    })
    var teamGroups = _.sortBy(group_data[0], 'name')
    const scoreboardTabTemplate = _.template(
      $("#scoreboard-tabs-template")
        .remove()
        .text()
    );
    var nav_content = scoreboardTabTemplate({
      eligibleScoreboards, teamGroups, renderScoreboard
    });
    $("#scoreboard-tabs").html(nav_content).promise().done(function(){
      // Attach listeners to tab links
      var tab_set = $("#scoreboard-tabs li a")
      tab_set.on("click", function(e) {
        $("#search").val("")
        var active_tab = $(e.target).parent().data();
        if (active_tab.sid !== undefined) {
          var board_key = {'scoreboard_id': active_tab.sid}
        }
        else if (active_tab.gid !== undefined) {
          var board_key = {'group_id': active_tab.gid}
        }
        reloadGraph()
        render_scoreboard(board_key)
      })

      // Attach search field listener
      $("form[role=search]").on("submit", function(e) {
        e.preventDefault();
        var active_tab = $("#scoreboard-tabs li.active").data();
        if (active_tab.sid !== undefined) {
          var board_key = {'scoreboard_id': active_tab.sid}
        }
        else if (active_tab.gid !== undefined) {
          var board_key = {'group_id': active_tab.gid}
        }
        var searchValue = $("#search").val();
        render_scoreboard(board_key, searchValue);
      });

      // Automatically render the first scoreboard
      tab_set.first().trigger("click")
    })
  })
  .fail(jqXHR =>
    apiNotify({ status: 0, message: jqXHR.responseJSON.message })
  );

$(function() {
  render_scoreboard_navigation();
});
