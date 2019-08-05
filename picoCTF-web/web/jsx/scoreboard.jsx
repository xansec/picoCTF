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

const load_teamscore = () =>
  apiCall("GET", "/api/v1/team")
    .done(data =>
      $("#scoreboard-teamscore").html(
        renderScoreboardTeamScore({
          teamscore: data.score
        })
      )
    )
    .fail(jqXHR =>
      apiNotify({ status: 0, message: jqXHR.responseJSON.message })
    );

window.reloadGraph = function() {
  const reload = function() {
    $(".progression-graph").empty();
    const active_tab = $("ul#scoreboard-tabs li.active").data();
    if (active_tab !== undefined) {
      const active_gid = active_tab.gid;
      window.drawTopTeamsProgressionGraph(
        `#${active_gid}-progression`,
        active_gid
      );
    }
  };

  setTimeout(reload, 100);
};

const load_scoreboard_page = function(boardname, page, tid, gid) {
  let targetid;
  if (gid == null) {
    gid = "";
  }
  if (!gid) {
    targetid = boardname;
  } else {
    boardname = "groups";
    targetid = gid;
  }
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

const load_scoreboard = () =>
  apiCall("GET", "/api/v1/stats/scoreboard")
    .done(function(data) {
      $("#scoreboard-tabs")
        .html(
          renderScoreboardTabs({
            data,
            renderScoreboard
          })
        )
        .promise()
        .then(function() {
          const { tid } = data;
          const paginate = board =>
            $(`#${board.name}-pagination`).bootstrapPaginator({
              totalPages: board.pages,
              bootstrapMajorVersion: 3,
              numberOfPages: 10,
              currentPage: board.start_page,
              onPageClicked(e, eOriginal, type, page) {
                load_scoreboard_page(
                  board.name,
                  page,
                  data.tid,
                  board.gid
                );
              }
            });
          Object.keys(data).forEach(function(e) {
            if (Array.isArray(data[e])) {
              data[e].forEach(paginate);
            } else if (typeof data[e] === "object") {
              paginate(data[e]);
            }
          });
          let timeoutID_global = null;
          let timeoutID_student = null;
          const paginateSearch = (pattern, board) =>
            $(`#${board.name}-pagination`).bootstrapPaginator({
              totalPages: Math.max(board.pages, 1),
              bootstrapMajorVersion: 3,
              numberOfPages: 10,
              currentPage: board.start_page,
              onPageClicked(e, eOriginal, type, page) {
                searchBoard(pattern, board.name, page);
              }
            });
          var searchBoard = function(pattern, board, page) {
            let repaginate;
            if (page == null) {
              page = 0;
            }
            if (page === 0) {
              repaginate = true;
              page = 1;
            }
            apiCall(
              "GET",
              `/api/v1/stats/scoreboard/search?pattern=${pattern}&board=${board}&page=${page}`
            ).done(function(searchdata) {
              $(`#${board} tbody`).html(
                renderScorepage({
                  scorepage: searchdata.scoreboard,
                  page,
                  tid
                })
              );
              if (repaginate) {
                paginateSearch(pattern, searchdata);
              }
            });
          };
          $("#global-search").keyup(function(e) {
            if (e.target.value.length > 2) {
              clearTimeout(timeoutID_global);
              timeoutID_global = setTimeout(
                () => searchBoard(e.target.value, "global"),
                250
              );
            } else if (e.target.value === "") {
              load_scoreboard();
              reloadGraph();
            }
          });
          $("#student-search").keyup(function(e) {
            if (e.target.value.length > 2) {
              clearTimeout(timeoutID_student);
              timeoutID_student = setTimeout(
                () => searchBoard(e.target.value, "student"),
                250
              );
            } else if (e.target.value === "") {
              load_scoreboard()
                .promise()
                .then(function() {
                  $('#scoreboard-tabs a[href="#student"]').tab("show");
                  reloadGraph();
                });
            }
          });
        });
      reloadGraph();
    })
    .fail(jqXHR =>
      apiNotify({ status: 0, message: jqXHR.responseJSON.message })
    );

$(function() {
  load_scoreboard();
  load_teamscore();
});
