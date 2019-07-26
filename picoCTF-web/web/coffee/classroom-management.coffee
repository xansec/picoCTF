Input = ReactBootstrap.Input
Row = ReactBootstrap.Row
Col = ReactBootstrap.Col
Button = ReactBootstrap.Button
ButtonGroup = ReactBootstrap.ButtonGroup
Panel = ReactBootstrap.Panel
ListGroup = ReactBootstrap.ListGroup
ListGroupItem = ReactBootstrap.ListGroupItem
Glyphicon = ReactBootstrap.Glyphicon
Tabs = ReactBootstrap.Tabs
Tab = ReactBootstrap.Tab

update = React.addons.update

MemberManagementItem = React.createClass
  removeTeam: ->
    data = {
      "team_id": @props.tid
    }
    apiCall "POST", "/api/v1/groups/" + @props.gid + "/remove_team", data
    .success ((data) ->
      apiNotify {"status": 1, "message": "Team has successfully left the classroom."}
      @props.refresh()
    ).bind this
    .error ((jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}
    ).bind this

  # switchUserRole: (tid, role) ->
  #   apiCall "POST", "/api/v1/group/teacher/role_switch", {gid: @props.gid, tid: tid, role: role}
  #   .done ((resp) ->
  #     apiNotify resp
  #     @props.refresh()
  #   ).bind this

  render: ->
    if @props.teacher
      userButton =
      <Button bsStyle="success" className="btn-sq">
        <Glyphicon glyph="user" bsSize="large"/>
        <p className="text-center">Teacher</p>
      </Button>
    else
      userButton =
      <Button bsStyle="primary" className="btn-sq">
        <Glyphicon glyph="user" bsSize="large"/>
        <p className="text-center">User</p>
      </Button>

    # if @props.teacher
    #   switchUser = <Button onClick={@switchUserRole.bind(null, @props.tid, "member")}>Make Member</Button>
    # else
    #   switchUser = <Button onClick={@switchUserRole.bind(null, @props.tid, "teacher")}>Make Teacher</Button>

    <ListGroupItem>
      <Row className="row">
        <Col xs={2}>
          {userButton}
        </Col>
        <Col xs={6}>
          <h4>{@props.team_name}</h4>
          <p><strong>Affiliation:</strong> {@props.affiliation}</p>
        </Col>
        <Col xs={4}>
          <ButtonGroup vertical>
            <Button onClick={@removeTeam}>Remove User</Button>
          </ButtonGroup>
        </Col>
      </Row>
    </ListGroupItem>

MemberInvitePanel = React.createClass
  mixins: [React.addons.LinkedStateMixin]

  propTypes:
    gid: React.PropTypes.string.isRequired

  getInitialState: ->
    role: "member"

  inviteUser: (e) ->
    e.preventDefault()
    data = {
      email: @state.email,
      as_teacher: (@state.role == "teacher")
    }
    apiCall "POST", "/api/v1/groups/" + @props.gid + "/invite", data
    .success ((data) ->
      apiNotify {"status": 1, "message": "Email invitation has been sent."}
      @setState update @state, $set: email: ""
      @props.refresh()
    ).bind this
    .error ((jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}
    ).bind this

  render: ->
    <Panel>
      <form onSubmit={@inviteUser}>
        <Col xs={8}>
          <Input type="email" label="E-mail" valueLink={@linkState "email"}/>
        </Col>
        <Col xs={4}>
          <Input type="select" label="Role" placeholder="Member" valueLink={@linkState "role"}>
            <option value="member">Member</option>
            <option value="teacher">Teacher</option>
          </Input>
        </Col>
        <Col xs={4}>
          <Button onClick={@inviteUser}>Invite User</Button>
        </Col>
      </form>
    </Panel>

BatchRegistrationPanel = React.createClass
  mixins: [React.addons.LinkedStateMixin]

  propTypes:
    gid: React.PropTypes.string.isRequired

  handleFileUpload: (e) ->
    e.preventDefault()
    formData = new FormData();
    formData.append('csv', this.refs.fileUpload.getInputDOMNode().files[0]);
    params = {
      method: "POST"
      url: "/api/v1/groups/" + @props.gid + "/batch_registration"
      data: formData
      cache: false
      contentType: false
      processData: false
    }
    $.ajax params
    .success ((data) ->
      response_html = '<div class="panel panel-success batch-registration-response"><div class="panel-heading"><h4>Accounts successfully created!</h4>' +
                      '<p>Usernames and passwords are displayed below in the order of the input CSV.</p>' +
                      '<p>Please copy these credentials, as they will only be displayed once.</p>' +
                      '<table class="table">'
      for i in [0...data.accounts.length]
        response_html += '<tr><td>' + data.accounts[i].username + '</td><td>' + data.accounts[i].password + '</td></tr>'
      response_html += '</table></div></div>'
      $('.batch-registration-response').remove()
      $('#batch-registration-panel').append(response_html)
      @props.refresh()
    ).bind this
    .error ((jqXHR) ->
      # If the error is a string
      if typeof(jqXHR.responseJSON.message) is 'string'
        apiNotify {"status": 0, "message": jqXHR.responseJSON.message}
        return
      # Otherwise, the error is an object of validation errors
      errors = jqXHR.responseJSON.message
      response_html = '<div class="panel panel-danger batch-registration-response"><div class="panel-heading"><h4>Errors found in CSV.</h4>' +
                      '<p>Please resolve the issues below and resubmit:</p>'
      for row_num, row of errors
        response_html += '<p><strong>Row ' + (parseInt(row_num) + 1) + ':</strong></p><ul>'
        for field, err_messages of row
          for err_message in err_messages
            if field == '_schema'
              response_html += '<li>' + _.escape(err_message) + '</li>'
            else
              response_html += '<li>' + _.escape(field) + ': ' + _.escape(err_message) + '</li>'
        response_html += '</ul>'
      $('.batch-registration-response').remove()
      $('#batch-registration-panel').append(response_html)
    ).bind this

  render: ->
    <Panel id="batch-registration-panel">
      <Row>
        <Col xs={12}>
          <p>{"Batch-register students into this classroom by uploading a CSV of student demographic information. Usernames and passwords will be automatically generated."}</p>
          <p>{"Please note that your account's email address will be associated with any student accounts created via batch registration."}</p>
        </Col>
      </Row>
      <Row>
        <Col xs={6}>
          <Button href="/files/picoctf_batch_import.csv">Download Template</Button>
        </Col>
        <Col xs={6}>
          <form>
            <Input type='file' label='Upload CSV' accept='.csv' ref='fileUpload'/>
            <Input type='submit' onClick={@handleFileUpload}/>
          </form>
        </Col>
      </Row>
    </Panel>

MemberManagement = React.createClass
  render: ->
    allMembers = update @props.teacherInformation, {$push: @props.memberInformation}
    allMembers = _.filter allMembers, ((member) -> @props.currentUser["tid"] != member["tid"]).bind this

    memberInformation = <ListGroup>
        {allMembers.map ((member, i) ->
          <MemberManagementItem key={i} gid={@props.gid} refresh={@props.refresh} {...member}/>
        ).bind this}
      </ListGroup>

    <Panel>
      <h4>User Management</h4>
      <MemberInvitePanel gid={@props.gid} refresh={@props.refresh}/>
      <h4>Batch Registration</h4>
      <BatchRegistrationPanel gid={@props.gid} refresh={@props.refresh}/>
      {memberInformation}
    </Panel>

GroupManagement = React.createClass
  getInitialState: ->
    name: ""
    settings:
      email_filter: []
      hidden: false
    member_information: []
    teacher_information: []
    current_user: {}

  componentWillMount: ->
    @refreshSettings()

  refreshSettings: ->
    apiCall "GET", "/api/v1/groups/" + @props.gid
    .success ((data) ->
      @setState update @state, settings: $set: data.settings
      @setState update @state, member_information: $set: data.members
      @setState update @state, teacher_information: $set: data.teachers
    ).bind this

    apiCall "GET", "/api/v1/user"
    .success ((data) ->
      @setState update @state, current_user: $set: data
      if not data["teacher"] or (window.userStatus and not window.userStatus.teacher)
        apiNotify {status: 1, message: "You are no longer a teacher."}, "/profile"
    ).bind this

  pushUpdates: (modifier) ->
    data = @state

    if modifier
      data.settings = modifier data.settings

    apiCall "PATCH", "/api/v1/groups/" + @props.gid, {settings: data.settings}
    .success ((data) ->
      apiNotify {"status": 1, "message": "Classroom settings changed successfully."}
      @refreshSettings()
    ).bind this
    .error ((jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}
    ).bind this

  render: ->
    <div className="row" style={ marginTop: "10px"}>
      <Col sm={6}>
        <MemberManagement teacherInformation={@state.teacher_information} currentUser={@state.current_user}
          memberInformation={@state.member_information} gid={@props.gid} refresh={@refreshSettings}/>
      </Col>
      <Col sm={6}>
        <GroupOptions pushUpdates={@pushUpdates} settings={@state.settings} gid={@props.gid}/>
        <GroupEmailWhitelist emails={@state.settings.email_filter} pushUpdates={@pushUpdates} gid={@props.gid}/>
      </Col>
    </div>

GroupOptions = React.createClass
  propTypes:
    settings: React.PropTypes.object.isRequired
    pushUpdates: React.PropTypes.func.isRequired
    gid: React.PropTypes.string.isRequired

  promptGroupHide: ->
    window.confirmDialog "This option will hide all members of this classroom from public or competition scoreboards. This change is irrevocable; you will not be able to change this back later.", "Hidden Classroom Change",
    "Okay", "Cancel", (() ->
      @props.pushUpdates ((data) -> update data, {hidden: {$set: true}})
    ).bind this, () -> false

  render: ->
    if @props.settings.hidden
      hiddenGroupDisplay =
        <p>This classroom is <b>hidden</b> from the general scoreboard.</p>
    else
      hiddenGroupDisplay =
        <p>
          This classroom is <b>visible</b> on the scoreboard.
          Click <a href="#" onClick={@promptGroupHide}>here</a> to hide it.
        </p>

    <Panel>
      <h4>Classroom Options</h4>
      <Panel>
        <form>
          {hiddenGroupDisplay}
        </form>
      </Panel>
    </Panel>

EmailWhitelistItem = React.createClass
  propTypes:
    email: React.PropTypes.string.isRequired
    pushUpdates: React.PropTypes.func.isRequired

  render: ->
    removeEmail = @props.pushUpdates.bind null, ((data) ->
      update data, {email_filter: {$apply: _.partial _.without, _, @props.email}}
    ).bind this

    <ListGroupItem>
      *@{@props.email}
      <span className="pull-right"><Glyphicon glyph="remove" onClick={removeEmail}/></span>
    </ListGroupItem>

GroupEmailWhitelist = React.createClass
  mixins: [React.addons.LinkedStateMixin]

  getInitialState: -> {}

  propTypes:
    pushUpdates: React.PropTypes.func.isRequired
    emails: React.PropTypes.array.isRequired
    gid: React.PropTypes.string.isRequired

  addEmailDomain: (e) ->
    # It would probably make more sense to this kind of validation server side.
    # However, it can't cause any real issue being here.

    e.preventDefault()

    if _.indexOf(@props.emails, @state.emailDomain) != -1
      apiNotify {status: 0, message: "This email domain has already been whitelisted."}
    else if _.indexOf(@state.emailDomain, "@") != -1
      apiNotify {status: 0, message: "You should not include '@'. I want the email domain that follows '@'."}
    else if _.indexOf(@state.emailDomain, ".") == -1
        apiNotify {status: 0, message: "Your email domain did not include a '.' as I expected. Please make sure this is an email domain."}
    else
      @props.pushUpdates ((data) ->
        #Fine because @setState won't affect the next line
        @setState update @state, $set: emailDomain: ""
        update data, email_filter: $push: [@state.emailDomain]
      ).bind this

  createItemDisplay: ->
    <ListGroup>
      {@props.emails.map ((email, i) ->
        <EmailWhitelistItem key={i} email={email} pushUpdates={@props.pushUpdates}/>
      ).bind this}
    </ListGroup>

  render: ->
    emptyItemDisplay =
      <p>The whitelist is current empty. All emails will be accepted during registration.</p>

    <div>
      <h4>Email Domain Whitelist</h4>
        <Panel>
          <form onSubmit={@addEmailDomain}>
            <Input type="text" addonBefore="@ Domain" valueLink={@linkState "emailDomain"}/>
            {if @props.emails.length > 0 then @createItemDisplay() else emptyItemDisplay}
          </form>
        </Panel>
    </div>

TeacherManagement = React.createClass
  getInitialState: ->
    groups: []
    tabKey: 0

  onTabSelect: (tab) ->
    @setState update @state, tabKey: $set: tab

  componentWillMount: ->
    apiCall "GET", "/api/v1/groups"
    .success ((data) ->
      @setState update @state, groups: $set: data
    ).bind this

  render: ->
    <Tabs activeKey={@state.tabKey} onSelect={@onTabSelect}>
      {@state.groups.map ((group, i) ->
        <Tab eventKey={i} key={i} tab={group.name} className="tab-pane-outline">
          <GroupManagement key={group.name} gid={group.gid}/>
        </Tab>
      ).bind this}
    </Tabs>
$ ->
  ReactDOM.render <TeacherManagement/>, document.getElementById "group-management"

  $(document).on 'shown.bs.tab', 'a[href="#group-management-tab"]', () ->
    ReactDOM.unmountComponentAtNode document.getElementById "group-management"
    ReactDOM.render <TeacherManagement/>, document.getElementById "group-management"

