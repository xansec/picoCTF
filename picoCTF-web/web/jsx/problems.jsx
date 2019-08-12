/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * DS208: Avoid top-level this
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
const { Panel } = ReactBootstrap;
const { Button } = ReactBootstrap;
const { ButtonGroup } = ReactBootstrap;
const { Glyphicon } = ReactBootstrap;
const { Col } = ReactBootstrap;
const { Input } = ReactBootstrap;
const { Label } = ReactBootstrap;
const { PanelGroup } = ReactBootstrap;
const { Row } = ReactBootstrap;
const { ListGroup } = ReactBootstrap;
const { ListGroupItem } = ReactBootstrap;
const { Collapse } = ReactBootstrap;
const { Table } = ReactBootstrap;
const { Badge } = ReactBootstrap;
const { Tab } = ReactBootstrap;
const { Nav } = ReactBootstrap;
const { NavItem } = ReactBootstrap;
const { FormGroup } = ReactBootstrap;
const { InputGroup } = ReactBootstrap;
const { FormControl } = ReactBootstrap;

const renderProblemList = _.template(
  $("#problem-list-template")
    .remove()
    .text()
);
const renderProblem = _.template(
  $("#problem-template")
    .remove()
    .text()
);
const renderProblemSubmit = _.template(
  $("#problem-submit-template")
    .remove()
    .text()
);
const renderAchievementMessage = _.template(
  $("#achievement-message-template")
    .remove()
    .text()
);

window.ratingMetrics = ["Difficulty", "Enjoyment", "Educational Value"];
window.ratingQuestion = {
  Difficulty: "How difficult is this problem?",
  Enjoyment: "Did you enjoy this problem?",
  "Educational Value": "How much did you learn while solving this problem?"
};
window.ratingChoices = {
  Difficulty: ["Too easy", "", "A bit challenging", "", "Very hard"],
  Enjoyment: ["Hated it!", "", "It was okay.", "", "Loved it!"],
  "Educational Value": [
    "Nothing at all",
    "",
    "Something useful",
    "",
    "Learned a lot!"
  ]
};

window.timeValues = [
  "5 minutes or less",
  "10 minutes",
  "20 minutes",
  "40 minutes",
  "1 hour",
  "2 hours",
  "3 hours",
  "4 hours",
  "5 hours",
  "6 hours",
  "8 hours",
  "10 hours",
  "15 hours",
  "20 hours",
  "30 hours",
  "40 hours or more"
];

const sanitizeMetricName = metric => metric.toLowerCase().replace(" ", "-");

const constructAchievementCallbackChainHelper = function(achievements, index) {
  $(".modal-backdrop").remove();
  if (index >= 0) {
    messageDialog(
      renderAchievementMessage({ achievement: achievements[index] }),
      "Achievement Unlocked!",
      "OK",
      () => constructAchievementCallbackChainHelper(achievements, index - 1)
    );
  }
};

const constructAchievementCallbackChain = achievements =>
  constructAchievementCallbackChainHelper(
    achievements,
    achievements.length - 1
  );

const submitProblem = function(e) {
  e.preventDefault();
  const input = $(e.target).find("input");
  apiCall("POST", "/api/v1/submissions", {
    pid: input.data("pid"),
    key: input.val(),
    method: "web"
  })
    .done(function(data) {
      if (data.correct) {
        ga("send", "event", "Problem", "Solve", "Basic");
        apiNotify({ status: 1, message: data.message });
        loadProblems();
      } else {
        ga("send", "event", "Problem", "Wrong", "Basic");
        apiNotify({ status: 0, message: data.message });
      }
    })
    .fail(jqXHR =>
      apiNotify({ status: 0, message: jqXHR.responseJSON.message })
    );
};

// apiCall "GET", "/api/v1/achievements"
// .done (data) ->
//   if data['status'] is 1
//     new_achievements = (x for x in data.data when !x.seen)
//     constructAchievementCallbackChain new_achievements

const addProblemReview = function(e) {
  const target = $(e.target);

  const pid = target.data("pid");
  const feedback = {
    liked: target.data("setting") === "up"
  };

  const postData = { feedback, pid };
  apiCall("POST", "/api/v1/feedback", postData)
    .done(function(data) {
      apiNotify({ status: 1, message: "Your feedback has been accepted." });
      const selector = `#${pid}-thumbs${feedback.liked ? "down" : "up"}`;
      $(selector).removeClass("active");
      target.addClass("active");
      ga("send", "event", "Problem", "Review", "Basic");
    })
    .fail(jqXHR =>
      apiNotify({ status: 0, message: jqXHR.responseJSON.message })
    );
};

// apiCall "GET", "/api/v1/achievements"
// .done (data) ->
//   if data['status'] is 1
//     new_achievements = (x for x in data.data when !x.seen)
//     constructAchievementCallbackChain new_achievements

const loadProblems = () =>
  apiCall("GET", "/api/v1/problems")
    .fail(jqXHR =>
      apiNotify({ status: 0, message: jqXHR.responseJSON.message })
    )
    .done(function(data) {
      // We want the score to be level with the title, but the title
      // is defined in a template. This solution is therefore a bit
      // of a hack.
      addScoreToTitle("#title");
      apiCall("GET", "/api/v1/feedback")
        .done(function(reviewData) {
          /*$("#problem-list-holder").html(
            renderProblemList({
              problems: data,
              reviewData,
              renderProblem,
              renderProblemSubmit,
              sanitizeMetricName
            })
          );*/
          ReactDOM.render(
            <ProblemView
              problems={data}
              reviewData={reviewData}
            />,
            document.getElementById("problem-list-holder")
          );

          $(".time-slider").slider({
            value: 4,
            min: 0,
            max: 15,
            step: 1,
            slide(event, ui) {
              $(`#${$(this).data("labelTarget")}`).html(
                window.timeValues[ui.value]
              );
            }
          });

          $(".time-slider").each(function(x) {
            $(`#${$(this).data("labelTarget")}`).html(
              window.timeValues[4]
            );
          });

          //Should solved problem descriptions still be able to be viewed?
          //$("li.disabled>a").removeAttr "href"

          $(".problem-hint").hide();
          $(".problem-submit").on("submit", submitProblem);

          $(".rating-button").on("click", addProblemReview);
        })
        .fail(jqXHR =>
          apiNotify({ status: 0, message: jqXHR.responseJSON.message })
        );
    });

const addScoreToTitle = selector =>
  apiCall("GET", "/api/v1/team/score").done(function(data) {
    if (data) {
      $(selector)
        .children("#team-score")
        .remove();
      $(selector).append(
        `<span id='team-score' class='pull-right'>Score: ${data.score}</span>`
      );
    }
  });

const ClassifierItem = React.createClass({
  handleClick(e) {
    this.props.setClassifier(
      !this.props.active,
      this.props.classifier,
      this.props.name
    );
    this.props.onExclusiveClick(this.props.name);
  },

  render() {
    const glyph = <Glyphicon glyph="ok" />;

    return (
      <ListGroupItem onClick={this.handleClick} className="classifier-item">
        {this.props.name} {this.props.active ? glyph : undefined}{" "}
        <div className="pull-right">
          <Badge>{this.props.size}</Badge>
        </div>
      </ListGroupItem>
    );
  }
});

const ProblemClassifier = React.createClass({
  getInitialState() {
    return _.object(
      this.props.data.map(classifier => [classifier.name, false])
    );
  },

  handleClick(name) {
    const activeStates = this.getInitialState();
    activeStates[name] = !this.state[name];
    this.setState(activeStates);
  },

  render() {
    return (
      <Panel header={this.props.name} defaultExpanded={true} collapsible={true}>
        <ListGroup fill={true}>
          {this.props.data.map((data, i) => {
            return (
              <ClassifierItem
                {...Object.assign(
                  {
                    onExclusiveClick: this.handleClick,
                    active: this.state[data.name],
                    key: i,
                    setClassifier: this.props.setClassifier
                  },
                  data
                )}
              />
            );
          })}
        </ListGroup>
      </Panel>
    );
  }
});

const ProblemClassifierList = React.createClass({
  render() {
    const categories = _.groupBy(this.props.problems, "category");
    let categoryData = _.map(categories, (problems, category) => ({
      name: `Only ${category}`,
      size: problems.length,
      classifier(problem) {
        return problem.category === category;
      }
    }));
    categoryData = _.sortBy(categoryData, "name");

    const solvedState = _.groupBy(this.props.problems, "solved");
    let solvedData = _.map(solvedState, (problems, solved) => ({
      name: `${solved ? "Solved" : "Unsolved"}`,
      size: problems.length,
      classifier(problem) {
        return problem.solved === solved;
      }
    }));
    //solvedData = _.sortBy(solvedData, "name");

    return (
      <PanelGroup className="problem-classifier" collapsible={true}>
        <ProblemClassifier
          {...Object.assign(
            { name: "Categories", data: categoryData },
            this.props
          )}
        />
        <ProblemClassifier
          {...Object.assign(
            { name: "Solved", data: solvedData },
            this.props
          )}
        />
      </PanelGroup>
    );
  }
});

const ProblemHintTable = React.createClass({
  render() {
    return (
      <Table responsive={true}>
        <thead>
          <tr>
            <th>#</th>
            <th>Hint</th>
          </tr>
        </thead>
        <tbody>
          {this.props.hints.map((hint, i) => (
            <tr key={i}>
              <td>{i + 1}</td>
              <td>{hint}</td>
            </tr>
          ))}
        </tbody>
      </Table>
    );
  }
});

const ProblemSubmit = React.createClass({
  render() {
    return (
      <Col>
        <p className="problem-description">{this.props.description}</p>
        <Row>
          <form class="problem-submit">
            <FormGroup>
              <Col md={10} sm={9} xs={7} lg={11}>
                <InputGroup>
                  <InputGroup.Button>
                    <Button className="btn-primary" type="submit">Submit!</Button>
                  </InputGroup.Button>
                  <FormControl
                    type="text"
                    value={this.state.value}
                    placeholder="picoCTF{FLAG}"
                    onChange={this.handleChange}
                  />
                </InputGroup>
              </Col>
              <Col md={2} sm={3} xs={5} lg={1}>
                <span id={this.props.pid + "-thumbsup"} data-pid={this.props.pid} data-setting="up" style="font-size:1.7em;" class={"rating-button glyphicon glyphicon-thumbs-up pull-left" + thumbs.upClass}></span>
                <span id={this.props.pid + "-thumbsdown"} data-pid={this.props.pid} data-setting="down" style="font-size:1.7em;" class={"rating-button glyphicon glyphicon-thumbs-down pull-right" + thumbs.downClass}></span>
              </Col>
            </FormGroup>
          </form>
        </Row>
      </Col>
    )
  }
})

const Problem = React.createClass({
  getInitialState() {
    return { expanded: false };
  },

  handleExpand(e) {
    e.preventDefault();

    //This is awkward.
    if (
      $(e.target)
        .parent()
        .hasClass("do-expand")
    ) {
      this.setState({ expanded: !this.state.expanded });
    }
  },

  render() {
    const problemHeader = (
      <div>
        <span className="do-expand">
          {this.props.name} - Points: {this.props.score} - (Solves: {this.props.solves})
        </span>
        <div className="pull-right">
          {this.props.category} - {this.props.solved ? "Solved" : "Unsolved"}
        </div>
      </div>
    );

    //Do something interesting here.
    const panelStyle = this.props.disabled ? "default" : "default";

    var alreadyReviewed = false;
    var review = null;

    for (var i = 0; i < this.props.reviewData.length; i++)
      if (this.props.reviewData[i].pid == problem.pid){
        alreadyReviewed = true;
        review = this.props.reviewData[i].feedback;
      }

    var thumbs = {
      upClass: alreadyReviewed && review.liked ? "active" : "",
      downClass: alreadyReviewed && !review.liked ? "active" : ""
    };

    if (this.state.expanded) {
      return (
        <Panel
          bsStyle={panelStyle}
          header={problemHeader}
          collapsible={true}
          expanded={this.state.expanded}
          onSelect={this.handleExpand}
        >
          <Row id={this.props.pid}>
            <Col>
              <Tab.Container defaultActiveKey={this.props.pid + "solve"}>
                <Row className="clearfix">
                  <Col sm={12}>
                    <Nav bsStyle="tabs">
                      <NavItem eventKey={this.props.pid + "solve"}>Solve</NavItem>
                      <NavItem eventKey={this.props.pid + "hint"}>Hints</NavItem>
                    </Nav>
                  </Col>
                  <Col sm={12}>
                    <Tab.Content>
                      <Tab.Pane eventKey={this.props.pid + "solve"}>
                        <Panel.Body>
                          <ProblemSubmit
                            {...Object.assign(
                              {
                                thumbs: thumbs
                              },
                              this.props
                            )}
                          />
                        </Panel.Body>
                      </Tab.Pane>
                      <Tab.Pane eventKey={this.props.pid + "hint"}>
                        <ProblemHintTable hints={this.props.hints} />
                      </Tab.Pane>
                    </Tab.Content>
                  </Col>
                </Row>
              </Tab.Container>
            </Col>
          </Row>
        </Panel>
      );
    } else {
      return (
        <Panel
          bsStyle={panelStyle}
          header={problemHeader}
          collapsible={true}
          expanded={this.state.expanded}
          onSelect={this.handleExpand}
        />
      );
    }
  }
});

const ProblemList = React.createClass({
  propTypes: {
    problems: React.PropTypes.array.isRequired
  },

  render() {
    if (this.props.problems.length === 0) {
      return (
        <h4>
          No problems have been loaded. Click <a href="#">here</a> to get
          started.
        </h4>
      );
    }

    const problemComponents = this.props.problems.map((problem, i) => {
      return (
        <Col key={i} xs={12}>
          <Problem
            {...Object.assign(
              {
                key: problem.name,
                reviewData: this.props.reviewData
              },
              problem
            )}
          />
        </Col>
      );
    });

    return <Row>{problemComponents}</Row>;
  }
});

const ProblemView = React.createClass({
  propTypes: {
    problems: React.PropTypes.array.isRequired
  },

  getInitialState() {
    return {
      problemClassifier: [
        {
          name: "all",
          func(problem) {
            return true;
          }
        }
      ]
    };
  },

  setClassifier(classifierState, classifier, name) {
    if (classifierState) {
      this.setState(
        update(this.state, {
          problemClassifier: { $push: [{ name, func: classifier }] }
        })
      );
    } else {
      const otherClassifiers = _.filter(
        this.state.problemClassifier,
        classifierObject => classifierObject.name !== name
      );
      this.setState(
        update(this.state, { problemClassifier: { $set: otherClassifiers } })
      );
    }
  },

  render() {
    return (
      <Row className="pad">
        <Col xs={3} md={3}>
          <ProblemClassifierList
            setClassifier={this.setClassifier}
            problems={this.props.problems}
          />
        </Col>
        <Col xs={9} md={9}>
          <ProblemList
            problems={this.props.problems}
            reviewData={this.props.reviewData}
          />
        </Col>
      </Row>
    );
  }
});


$(() => loadProblems());
