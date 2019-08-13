const renderScoreboardTeamScore = _.template(
  $("#scoreboard-teamscore-template")
    .remove()
    .text()
);
const renderScoreboardTabs = _.template(
  $("#scoreboard-tabs-template")
    .remove()
    .text()
);
const renderScoreboard = _.template(
  $("#scoreboard-template")
    .remove()
    .text()
);
const renderScorepage = _.template(
  $("#scorepage-template")
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

const render_scoreboard_page = function(board_key, search, page, tid) {
  apiCall(
    "GET",
    `/api/v1/stats/scoreboard/page?board=${boardname}&page=${page}&gid=${gid}`
  )
  .done(data =>
      $(`#${targetid} tbody`).html(
        renderScorepage({
          scorepage: data.scoreboard,
          page,
          tid
        })
      )
    )
  .fail(jqXHR =>
    apiNotify({ status: 0, message: jqXHR.responseJSON.message })
  );
};

const render_scoreboard_content = () =>
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
    eligibleScoreboards = _.sortBy(eligibleScoreboards, 'priority')
    var teamGroups = _.sortBy(group_data[0], 'name')
    $("#scoreboard-tabs").html(
      renderScoreboardTabs({
        eligibleScoreboards, teamGroups, renderScoreboard
      })
    )
  })
  .fail(jqXHR =>
    apiNotify({ status: 0, message: jqXHR.responseJSON.message })
  );

  // apiCall("GET", "/api/v1/stats/scoreboard")
  //   .done(function(data) {
  //     $("#scoreboard-tabs")
  //       .html(
  //         renderScoreboardTabs({
  //           data,
  //           renderScoreboard
  //         })
  //       )
  //       .promise()
  //       .then(function() {
  //         const { tid } = data;
  //         const paginate = board =>
  //           $(`#${board.name}-pagination`).bootstrapPaginator({
  //             totalPages: board.pages,
  //             bootstrapMajorVersion: 3,
  //             numberOfPages: 10,
  //             currentPage: board.start_page,
  //             onPageClicked(e, eOriginal, type, page) {
  //               load_scoreboard_page(
  //                 board.name,
  //                 page,
  //                 data.tid,
  //                 board.gid
  //               );
  //             }
  //           });
  //         Object.keys(data).forEach(function(e) {
  //           if (Array.isArray(data[e])) {
  //             data[e].forEach(paginate);
  //           } else if (typeof data[e] === "object") {
  //             paginate(data[e]);
  //           }
  //         });
  //         let timeoutID_global = null;
  //         let timeoutID_student = null;
  //         const paginateSearch = (pattern, board) =>
  //           $(`#${board.name}-pagination`).bootstrapPaginator({
  //             totalPages: Math.max(board.pages, 1),
  //             bootstrapMajorVersion: 3,
  //             numberOfPages: 10,
  //             currentPage: board.start_page,
  //             onPageClicked(e, eOriginal, type, page) {
  //               searchBoard(pattern, board.name, page);
  //             }
  //           });
  //         var searchBoard = function(pattern, board, page) {
  //           let repaginate;
  //           if (page == null) {
  //             page = 0;
  //           }
  //           if (page === 0) {
  //             repaginate = true;
  //             page = 1;
  //           }
  //           apiCall(
  //             "GET",
  //             `/api/v1/stats/scoreboard/search?pattern=${pattern}&board=${board}&page=${page}`
  //           ).done(function(searchdata) {
  //             $(`#${board} tbody`).html(
  //               renderScorepage({
  //                 scorepage: searchdata.scoreboard,
  //                 page,
  //                 tid
  //               })
  //             );
  //             if (repaginate) {
  //               paginateSearch(pattern, searchdata);
  //             }
  //           });
  //         };
  //         $("#global-search").keyup(function(e) {
  //           if (e.target.value.length > 2) {
  //             clearTimeout(timeoutID_global);
  //             timeoutID_global = setTimeout(
  //               () => searchBoard(e.target.value, "global"),
  //               250
  //             );
  //           } else if (e.target.value === "") {
  //             load_scoreboards();
  //             reloadGraph();
  //           }
  //         });
  //         $("#student-search").keyup(function(e) {
  //           if (e.target.value.length > 2) {
  //             clearTimeout(timeoutID_student);
  //             timeoutID_student = setTimeout(
  //               () => searchBoard(e.target.value, "student"),
  //               250
  //             );
  //           } else if (e.target.value === "") {
  //             load_scoreboards()
  //               .promise()
  //               .then(function() {
  //                 $('#scoreboard-tabs a[href="#student"]').tab("show");
  //                 reloadGraph();
  //               });
  //           }
  //         });
  //       });
  //     reloadGraph();
  //   })
  //   .fail(jqXHR =>
  //     apiNotify({ status: 0, message: jqXHR.responseJSON.message })
  //   );

$(function() {
  render_scoreboard_content();
});
