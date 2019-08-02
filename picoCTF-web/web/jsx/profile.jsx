const renderTeamInformation = _.template(
  $("#team-info-template")
    .remove()
    .text()
);
const renderGroupInformation = _.template(
  $("#group-info-template")
    .remove()
    .text()
);
const renderAchievementInformation = _.template(
  $("#achievement-info-template")
    .remove()
    .text()
);

const load_group_info = () =>
  apiCall("GET", "/api/v1/groups", null, "Team", "GroupLoad")
    .error(jqXHR =>
      apiNotify({ status: 0, message: jqXHR.responseJSON.message })
    )
    .success(function(data) {
      $("#group-info").html(renderGroupInformation({ data }));

      $("#join-group").on("click", group_request);
      $("#group-request-form").on("submit", join_group_request);
      $(".leave-group-span").on("click", e =>
        leave_group($(e.target).data("gid"))
      );
    });

// load_achievement_info = ->
//     apiCall "GET", "/api/v1/achievements"
//     .done (data) ->
//       switch data['status']
//         when 0
//             apiNotify(data)
//             ga('send', 'event', 'Achievements', 'LoadFailure', data.message);
//         when 1
//             $("#achievement-info").html renderAchievementInformation({data: data.data})

const join_group = function(group_name, group_owner) {
  const data = { group_name: group_name, group_owner: group_owner };
  apiCall("POST", "/api/v1/team/join_group", data, "Team", "JoinGroup")
    .success(function(data) {
      apiNotify({ status: 1, message: "Successfully joined group" });
      load_group_info();
    })
    .error(jqXHR =>
      apiNotify({ status: 0, message: jqXHR.responseJSON.message })
    );
};

const leave_group = gid =>
  apiCall(
    "GET",
    `/api/v1/groups/${gid}/remove_team`,
    null,
    "Team",
    "LeaveGroup"
  )
    .success(function(data) {
      apiNotify({ status: 1, message: "Successfully left group" });
      load_group_info();
    })
    .error(jqXHR =>
      apiNotify({ status: 0, message: jqXHR.responseJSON.message })
    );

const group_request = function(e) {
  e.preventDefault();
  const form = $(this).closest("form");
  confirmDialog(
    "By joining a class you are allowing the instructor to see statistics concerning your team's performance, " +
    "as well as information on your team members such as username and email. Are you sure you want to join this class?",
    "Class Confirmation",
    "Join",
    "Cancel",
    e => form.trigger("submit"),
    e => ga("send", "event", "Team", "JoinGroup", "RejectPrompt")
  );
};

const join_group_request = function(e) {
  e.preventDefault();

  const group_name = $("#group-name-input").val();
  const group_owner = $("#group-owner-input").val();
  join_group(group_name, group_owner);
};

const { update } = React.addons;
const { Panel } = ReactBootstrap;
const { ProgressBar } = ReactBootstrap;
const { Glyphicon } = ReactBootstrap;
const { Row } = ReactBootstrap;
const { Col } = ReactBootstrap;

const ProblemInfo = React.createClass({
  getInitialState() {
    return {
      solvedProblems: [],
      problems: [],
      team: {},
      user: {}
    };
  },

  componentWillMount() {
    apiCall("GET", "/api/v1/team")
      .success(data => {
        this.setState(update(this.state, { team: { $set: data } }));
      })
      .error(jqXHR =>
        apiNotify({ status: 0, message: jqXHR.responseJSON.message })
      );

    apiCall("GET", "/api/v1/problems")
      .success(data => {
        this.setState(update(this.state, { problems: { $set: data } }));
      })
      .error(jqXHR =>
        apiNotify({ status: 0, message: jqXHR.responseJSON.message })
      );

    apiCall("GET", "/api/v1/problems?solved_only=true")
      .success(data => {
        this.setState(
          update(this.state, { solvedProblems: { $set: data } })
        );
      })
      .error(jqXHR =>
        apiNotify({ status: 0, message: jqXHR.responseJSON.message })
      );

    addAjaxListener("problemInfoState", "/api/v1/user", data => {
      this.setState(update(this.state, { user: { $set: data } }));
    });
  },

  render() {
    let panelHeader;
    const allProblemsByCategory = _.groupBy(this.state.problems, "category");
    const solvedProblemsByCategory = _.groupBy(
      this.state.solvedProblems,
      "category"
    );

    const categories = _.keys(allProblemsByCategory);

    const styles = ["success", "info", "primary", "warning", "danger"];

    const glyphs = {
      Cryptography: "/img/lock.svg",
      "Web Exploitation": "/img/browser.svg",
      "Binary Exploitation": "/img/binary.svg",
      "Reverse Engineering": "/img/reversecog.svg",
      Forensics: "/img/search.svg",
      Tutorial: "/img/laptop.svg"
    };

    if (
      this.state.team &&
      this.state.team.length > 0 &&
      this.state.user.username !== this.state.team.team_name &&
      this.state.team.team_name.length > 0
    ) {
      panelHeader = (
        <div>
          Progress Overview
          <span className="pull-right">
            Team: <b>{this.state.team.team_name}</b>
          </span>
        </div>
      );
    } else {
      panelHeader = <div>Progress Overview</div>;
    }

    return (
      <Panel key={categories} header={panelHeader}>
        {categories.map(function(category, i) {
          const currentlySolved = solvedProblemsByCategory[category]
            ? solvedProblemsByCategory[category].length
            : 0;
          return (
            <Row key={i}>
              <Col xs={8} sm={8} md={6} lg={8} className="progress-container">
                <ProgressBar
                  now={currentlySolved}
                  bsStyle={styles[i % styles.length]}
                  max={allProblemsByCategory[category].length}
                  label="%(now)s / %(max)s"
                />
              </Col>
              <Col xs={4} sm={4} md={6} lg={4} className="progress-label">
                <img
                  className="category-icon"
                  src={glyphs[category] ? glyphs[category] : "/img/laptop.svg"}
                />
                <div className="pull-right">{category}</div>
              </Col>
            </Row>
          );
        })}
      </Panel>
    );
  }
});

$(function() {
  addAjaxListener("isTeacher", "/api/v1/user", function (data) {
    if (data.teacher) {
      window.isTeacher = true;
    }
    window.username = data.username;
  });

  //load_team_info()
  ReactDOM.render(<ProblemInfo />, document.getElementById("progress-info"));
  load_group_info();
  // load_achievement_info()
  window.drawTeamProgressionGraph(
    "#team-progression-graph",
    "#team-progression-graph-container"
  );
});
