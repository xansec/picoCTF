const { Input } = ReactBootstrap;
const { Row } = ReactBootstrap;
const { Col } = ReactBootstrap;
const { Button } = ReactBootstrap;
const { ButtonGroup } = ReactBootstrap;
const { Panel } = ReactBootstrap;
const { ListGroup } = ReactBootstrap;
const { ListGroupItem } = ReactBootstrap;
const { Glyphicon } = ReactBootstrap;
const { Tabs } = ReactBootstrap;
const { Tab } = ReactBootstrap;

const { update } = React.addons;

const MemberManagementItem = React.createClass({
  removeTeam() {
    const data = {
      team_id: this.props.tid
    };
    apiCall("POST", `/api/v1/groups/${this.props.gid}/remove_team`, data)
      .success(data => {
        apiNotify({
          status: 1,
          message: "Team has successfully left the classroom."
        });
        this.props.refresh();
      })
      .error(jqXHR => {
        apiNotify({ status: 0, message: jqXHR.responseJSON.message });
      });
  },

  // switchUserRole: (tid, role) ->
  //   apiCall "POST", "/api/v1/group/teacher/role_switch", {gid: @props.gid, tid: tid, role: role}
  //   .done ((resp) ->
  //     apiNotify resp
  //     @props.refresh()
  //   ).bind this

  render() {
    let userButton;
    if (this.props.teacher) {
      userButton = (
        <Button bsStyle="success" className="btn-sq">
          <Glyphicon glyph="user" bsSize="large" />
          <p className="text-center">Teacher</p>
        </Button>
      );
    } else {
      userButton = (
        <Button bsStyle="primary" className="btn-sq">
          <Glyphicon glyph="user" bsSize="large" />
          <p className="text-center">User</p>
        </Button>
      );
    }

    // if @props.teacher
    //   switchUser = <Button onClick={@switchUserRole.bind(null, @props.tid, "member")}>Make Member</Button>
    // else
    //   switchUser = <Button onClick={@switchUserRole.bind(null, @props.tid, "teacher")}>Make Teacher</Button>

    return (
      <ListGroupItem>
        <Row className="row">
          <Col xs={2}>{userButton}</Col>
          <Col xs={6}>
            <h4>{this.props.team_name}</h4>
            <p>
              <strong>Affiliation:</strong> {this.props.affiliation}
            </p>
          </Col>
          <Col xs={4}>
            <ButtonGroup vertical={true}>
              <Button onClick={this.removeTeam}>Remove User</Button>
            </ButtonGroup>
          </Col>
        </Row>
      </ListGroupItem>
    );
  }
});

const MemberInvitePanel = React.createClass({
  mixins: [React.addons.LinkedStateMixin],

  propTypes: {
    gid: React.PropTypes.string.isRequired
  },

  getInitialState() {
    return { role: "member" };
  },

  inviteUser(e) {
    e.preventDefault();
    const data = {
      email: this.state.email,
      as_teacher: this.state.role === "teacher"
    };
    apiCall("POST", `/api/v1/groups/${this.props.gid}/invite`, data)
      .success(data => {
        apiNotify({ status: 1, message: "Email invitation has been sent." });
        this.setState(update(this.state, { $set: { email: "" } }));
        this.props.refresh();
      })
      .error(jqXHR => {
        apiNotify({ status: 0, message: jqXHR.responseJSON.message });
      });
  },

  render() {
    return (
      <Panel>
        <form onSubmit={this.inviteUser}>
          <Col xs={8}>
            <Input
              type="email"
              label="E-mail"
              valueLink={this.linkState("email")}
            />
          </Col>
          <Col xs={4}>
            <Input
              type="select"
              label="Role"
              placeholder="Member"
              valueLink={this.linkState("role")}
            >
              <option value="member">Member</option>
              <option value="teacher">Teacher</option>
            </Input>
          </Col>
          <Col xs={4}>
            <Button onClick={this.inviteUser}>Invite User</Button>
          </Col>
        </form>
      </Panel>
    );
  }
});

const BatchRegistrationPanel = React.createClass({
  mixins: [React.addons.LinkedStateMixin],

  propTypes: {
    gid: React.PropTypes.string.isRequired
  },

  handleFileUpload(e) {
    e.preventDefault();
    const formData = new FormData();
    formData.append("csv", this.refs.fileUpload.getInputDOMNode().files[0]);
    const params = {
      method: "POST",
      url: `/api/v1/groups/${this.props.gid}/batch_registration`,
      data: formData,
      cache: false,
      contentType: false,
      processData: false
    };
    $.ajax(params)
      .success(data => {
        let response_html =
          '<div class="panel panel-success batch-registration-response"><div class="panel-heading"><h4>Accounts successfully created!</h4>' +
          "<p>Usernames and passwords are displayed below in the order of the input CSV.</p>" +
          "<p>Please copy these credentials, as they will only be displayed once.</p>" +
          '<table class="table">';
        for (let i = 0; i < data.accounts.length; i++) {
          response_html += `<tr><td>${data.accounts[i].username}</td><td>${data.accounts[i].password}</td></tr>`;
        }
        response_html += "</table></div></div>";
        $(".batch-registration-response").remove();
        $("#batch-registration-panel").append(response_html);
        this.props.refresh();
      })
      .error(jqXHR => {
        // If the error is a string
        if (typeof jqXHR.responseJSON.message === "string") {
          apiNotify({ status: 0, message: jqXHR.responseJSON.message });
          return;
        }
        // Otherwise, the error is an object of validation errors
        const errors = jqXHR.responseJSON.message;
        let response_html =
          '<div class="panel panel-danger batch-registration-response"><div class="panel-heading"><h4>Errors found in CSV.</h4>' +
          "<p>Please resolve the issues below and resubmit:</p>";
        for (let row_num in errors) {
          const row = errors[row_num];
          response_html += `<p><strong>Row ${parseInt(row_num) +
            1}:</strong></p><ul>`;
          for (let field in row) {
            const err_messages = row[field];
            for (let err_message of err_messages) {
              if (field === "_schema") {
                response_html += `<li>${_.escape(err_message)}</li>`;
              } else {
                response_html += `<li>${_.escape(field)}: ${_.escape(
                  err_message
                )}</li>`;
              }
            }
          }
          response_html += "</ul>";
        }
        $(".batch-registration-response").remove();
        $("#batch-registration-panel").append(response_html);
      });
  },

  render() {
    return (
      <Panel id="batch-registration-panel">
        <Row>
          <Col xs={12}>
            <p>
              Batch-register students into this classroom by uploading a CSV of
              student demographic information. Usernames and passwords will be
              automatically generated.
            </p>
            <p>
              Please note that your account's email address will be associated
              with any student accounts created via batch registration.
            </p>
          </Col>
        </Row>
        <Row>
          <Col xs={6}>
            <Button href="/files/picoctf_batch_import.csv">
              Download Template
            </Button>
          </Col>
          <Col xs={6}>
            <form>
              <Input
                type="file"
                label="Upload CSV"
                accept=".csv"
                ref="fileUpload"
              />
              <Input type="submit" onClick={this.handleFileUpload} />
            </form>
          </Col>
        </Row>
      </Panel>
    );
  }
});

const MemberManagement = React.createClass({
  render() {
    let allMembers = update(this.props.teacherInformation, {
      $push: this.props.memberInformation
    });
    allMembers = _.filter(allMembers, member => {
      return this.props.currentUser["tid"] !== member["tid"];
    });

    const memberInformation = (
      <ListGroup>
        {allMembers.map((member, i) => {
          return (
            <MemberManagementItem
              {...Object.assign(
                { key: i, gid: this.props.gid, refresh: this.props.refresh },
                member
              )}
            />
          );
        })}
      </ListGroup>
    );

    return (
      <Panel>
        <h4>User Management</h4>
        <MemberInvitePanel gid={this.props.gid} refresh={this.props.refresh} />
        <h4>Batch Registration</h4>
        <BatchRegistrationPanel
          gid={this.props.gid}
          refresh={this.props.refresh}
        />
        {memberInformation}
      </Panel>
    );
  }
});

const GroupManagement = React.createClass({
  getInitialState() {
    return {
      name: "",
      settings: {
        email_filter: [],
        hidden: false
      },
      member_information: [],
      teacher_information: [],
      current_user: {}
    };
  },

  componentWillMount() {
    this.refreshSettings();
  },

  refreshSettings() {
    apiCall("GET", `/api/v1/groups/${this.props.gid}`).success(data => {
      this.setState(update(this.state, { settings: { $set: data.settings } }));
      this.setState(
        update(this.state, { member_information: { $set: data.members } })
      );
      this.setState(
        update(this.state, { teacher_information: { $set: data.teachers } })
      );
    });

    /*
    apiCall("GET", "/api/v1/user").success(data => {
      this.setState(update(this.state, { current_user: { $set: data } }));
      if (!data["teacher"]) {
        apiNotify(
          { status: 1, message: "You are no longer a teacher." },
          "/profile"
        );
      }
    }); */
  },

  pushUpdates(modifier) {
    const data = this.state;

    if (modifier) {
      data.settings = modifier(data.settings);
    }

    apiCall("PATCH", `/api/v1/groups/${this.props.gid}`, {
      settings: data.settings
    })
      .success(data => {
        apiNotify({
          status: 1,
          message: "Classroom settings changed successfully."
        });
        this.refreshSettings();
      })
      .error(jqXHR => {
        apiNotify({ status: 0, message: jqXHR.responseJSON.message });
      });
  },

  render() {
    return (
      <div className="row" style={{ marginTop: "10px" }}>
        <Col sm={6}>
          <MemberManagement
            teacherInformation={this.state.teacher_information}
            currentUser={this.state.current_user}
            memberInformation={this.state.member_information}
            gid={this.props.gid}
            refresh={this.refreshSettings}
          />
        </Col>
        <Col sm={6}>
          <GroupOptions
            pushUpdates={this.pushUpdates}
            settings={this.state.settings}
            gid={this.props.gid}
          />
          <GroupEmailWhitelist
            emails={this.state.settings.email_filter}
            pushUpdates={this.pushUpdates}
            gid={this.props.gid}
          />
        </Col>
      </div>
    );
  }
});

const GroupOptions = React.createClass({
  propTypes: {
    settings: React.PropTypes.object.isRequired,
    pushUpdates: React.PropTypes.func.isRequired,
    gid: React.PropTypes.string.isRequired
  },

  promptGroupHide() {
    return window.confirmDialog(
      "This option will hide all members of this classroom from public or competition scoreboards. This change is irrevocable; you will not be able to change this back later.",
      "Hidden Classroom Change",
      "Okay",
      "Cancel",
      function() {
        this.props.pushUpdates(data =>
          update(data, { hidden: { $set: true } })
        );
      }.bind(this)
    );
  },

  render() {
    let hiddenGroupDisplay;
    if (this.props.settings.hidden) {
      hiddenGroupDisplay = (
        <p>
          This classroom is <b>hidden</b> from the general scoreboard.
        </p>
      );
    } else {
      hiddenGroupDisplay = (
        <p>
          <span>This classroom is <b>visible</b> on the scoreboard. Click </span>
          <a href="#" onClick={this.promptGroupHide}>here</a>
          <span> to hide it.</span>
        </p>
      );
    }

    return (
      <Panel>
        <h4>Classroom Options</h4>
        <Panel>
          <form>{hiddenGroupDisplay}</form>
        </Panel>
      </Panel>
    );
  }
});

const EmailWhitelistItem = React.createClass({
  propTypes: {
    email: React.PropTypes.string.isRequired,
    pushUpdates: React.PropTypes.func.isRequired
  },

  render() {
    const removeEmail = this.props.pushUpdates.bind(null, data => {
      update(data, {
        email_filter: { $apply: _.partial(_.without, _, this.props.email) }
      });
    });

    return (
      <ListGroupItem>
        *@
        {this.props.email}
        <span className="pull-right">
          <Glyphicon glyph="remove" onClick={removeEmail} />
        </span>
      </ListGroupItem>
    );
  }
});

const GroupEmailWhitelist = React.createClass({
  mixins: [React.addons.LinkedStateMixin],

  getInitialState() {
    return {};
  },

  propTypes: {
    pushUpdates: React.PropTypes.func.isRequired,
    emails: React.PropTypes.array.isRequired,
    gid: React.PropTypes.string.isRequired
  },

  addEmailDomain(e) {
    // It would probably make more sense to this kind of validation server side.
    // However, it can't cause any real issue being here.

    e.preventDefault();

    if (_.indexOf(this.props.emails, this.state.emailDomain) !== -1) {
      apiNotify({
        status: 0,
        message: "This email domain has already been whitelisted."
      });
    } else if (_.indexOf(this.state.emailDomain, "@") !== -1) {
      apiNotify({
        status: 0,
        message:
          "You should not include '@'. I want the email domain that follows '@'."
      });
    } else if (_.indexOf(this.state.emailDomain, ".") === -1) {
      apiNotify({
        status: 0,
        message:
          "Your email domain did not include a '.' as I expected. Please make sure this is an email domain."
      });
    } else {
      this.props.pushUpdates(data => {
        //Fine because @setState won't affect the next line
        this.setState(update(this.state, { $set: { emailDomain: "" } }));
        update(data, {
          email_filter: { $push: [this.state.emailDomain] }
        });
      });
    }
  },

  createItemDisplay() {
    return (
      <ListGroup>
        {this.props.emails.map((email, i) => {
          return (
            <EmailWhitelistItem
              key={i}
              email={email}
              pushUpdates={this.props.pushUpdates}
            />
          );
        })}
      </ListGroup>
    );
  },

  render() {
    const emptyItemDisplay = (
      <p>
        The whitelist is current empty. All emails will be accepted during
        registration.
      </p>
    );

    return (
      <div>
        <h4>Email Domain Whitelist</h4>
        <Panel>
          <form onSubmit={this.addEmailDomain}>
            <Input
              type="text"
              addonBefore="@ Domain"
              valueLink={this.linkState("emailDomain")}
            />
            {this.props.emails.length > 0
              ? this.createItemDisplay()
              : emptyItemDisplay}
          </form>
        </Panel>
      </div>
    );
  }
});

const TeacherManagement = React.createClass({
  getInitialState() {
    return {
      groups: [],
      tabKey: 0
    };
  },

  onTabSelect(tab) {
    this.setState(update(this.state, { tabKey: { $set: tab } }));
  },

  componentDidMount() {
    addAjaxListener("/api/v1/groups", data => {
      this.setState(update(this.state, { groups: { $set: data } }));
    });
  },

  render() {
    return (
      <Tabs activeKey={this.state.tabKey} onSelect={this.onTabSelect}>
        {this.state.groups.map((group, i) => {
          return (
            <Tab
              eventKey={i}
              key={i}
              title={group.name}
              className="tab-pane-outline"
            >
              <GroupManagement key={group.name} gid={group.gid} />
            </Tab>
          );
        })}
      </Tabs>
    );
  }
});
$(function() {
  ReactDOM.render(
    <TeacherManagement />,
    document.getElementById("group-management")
  );

  $(document).on(
    "shown.bs.tab",
    'a[href="#group-management-tab"]',
    function() {
      ReactDOM.unmountComponentAtNode(
        document.getElementById("group-management")
      );
      ReactDOM.render(
        <TeacherManagement />,
        document.getElementById("group-management")
      );
    }
  );
});
