updatePassword = (e) ->
  e.preventDefault()
  data = {
    "current_password": $("#current-password").val(),
    "new_password": $("#new-password").val(),
    "new_password_confirmation": $("#new-password-confirmation").val()
  }
  apiCall "POST", "/api/v1/user/update_password", data, 'Authentication', 'UpdatePassword'
  .success (data) ->
    apiNotify {"status": 1, "message": "Your password has been successfully updated!"}, "/account"
  .error (jqXHR) ->
    apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

resetPassword = (e) ->
  e.preventDefault()
  data = {
    "reset_token": window.location.hash.substring(1)
    "new_password": $("#password-reset-form input[name=new-password]").val()
    "new_password_confirmation": $("#password-reset-form input[name=new-password-confirmation]").val()
  }
  apiCall "POST", "/api/v1/user/reset_password", data, 'Authentication', 'ResetPassword'
  .done (data) ->
    ga('send', 'event', 'Authentication', 'ResetPassword', 'Success')
    apiNotify {"status": 1, "message": "Your password has been reset"}, "/"
  .error (jqXHR) ->
    apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

disableAccount = (e) ->
  e.preventDefault()
  confirmDialog "This will disable your account, drop you from your team, and prevent you from playing!", "Disable Account Confirmation", "Disable Account", "Cancel", () ->
    data = {
      "password": $("#disable-account-form input[name=current-password]").val()
    }
    apiCall "POST", "/api/v1/user/disable_account", data, 'Authentication', 'DisableAccount'
    .success (data) ->
      apiNotify {"status": 1, "message": "Your account has been disabled"}, "/"
    .error (jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

Input = ReactBootstrap.Input
Row = ReactBootstrap.Row
Col = ReactBootstrap.Col
Button = ReactBootstrap.Button
Panel = ReactBootstrap.Panel
Glyphicon = ReactBootstrap.Glyphicon
ButtonInput = ReactBootstrap.ButtonInput
ButtonGroup = ReactBootstrap.ButtonGroup

update = React.addons.update

# Should figure out how we want to share components.
TeamManagementForm = React.createClass
  mixins: [React.addons.LinkedStateMixin]

  getInitialState: ->
    user: {}
    team: {}
    team_name: ""
    team_password: ""

  componentWillMount: ->
    apiCall "GET", "/api/v1/user"
    .success ((data) ->
      @setState update @state,
        user: $set: data
    ).bind this

    apiCall "GET", "/api/v1/team"
    .success ((data) ->
      @setState update @state,
        team: $set: data
    ).bind this

  onTeamRegistration: (e) ->
    e.preventDefault()
    if (!@state.team_name || !@state.team_password)
      apiNotify({status: 0, message: "Invalid team name or password."})
    else
      data = {team_name: @state.team_name, team_password: @state.team_password}
      apiCall "POST", "/api/v1/teams", data
      .success (data) ->
        document.location.href = "/profile"
      .error (jqXHR) ->
        apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

  onTeamJoin: (e) ->
    e.preventDefault()
    data = {team_name: @state.team_name, team_password: @state.team_password}
    apiCall "POST", "/api/v1/team/join", data
    .success (data) ->
      document.location.href = "/profile"
    .error (jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}


  onTeamPasswordChange: (e) ->
    e.preventDefault()
    if @state.team_password != @state.confirm_team_password
      apiNotify {status: 0, message: "Passwords do not match."}
    else
      newpass = @state.team_password
      newpass_confirm = @state.confirm_team_password
      confirmDialog "This will change the password needed to join your team.", "Team Password Change Confirmation", "Confirm", "Cancel",
      () ->
        data = {"new_password": newpass, "new_password_confirmation": newpass_confirm}
        apiCall "POST", "/api/v1/team/update_password", data
        .success (data) ->
          apiNotify {"status": 1, "message": "Your team password has been successfully updated!"}, "/account"
        .error (jqXHR) ->
          apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

  listMembers: () ->
    for member in @state.team["members"]
      <li>{member.username} (<span className="capitalize">{member.usertype} - {member.country}</span>)</li>

  render: ->
    if @state.team.max_team_size > 1 and not @state.user.teacher
      window.$("#team-management-container").show()
      towerGlyph = <Glyphicon glyph="tower"/>
      lockGlyph = <Glyphicon glyph="lock"/>

      teamCreated = (@state.user and @state.user.username != @state.team.team_name)
      if teamCreated
        <Panel header="Team Management">
        <p><strong>Team Name:</strong> {@state.team.team_name}</p>
        <p><strong>Members</strong> ({@state.team.members.length}/{@state.team.max_team_size}):</p>
        <ul>
          {@listMembers()}
        </ul>

        <hr/>
          <form onSubmit={@onTeamPasswordChange}>
            <Input type="password" valueLink={@linkState "team_password"} addonBefore={lockGlyph} label="New Team Password" required/>
            <Input type="password" valueLink={@linkState "confirm_team_password"} addonBefore={lockGlyph} label="Confirm New Team Password" required/>
            <Col md={6}>
                <Button type="submit">Change Team Password</Button>
            </Col>
          </form>
        </Panel>
      else
        <Panel header="Team Management">
        <p>Your team name may be visible to other users. Do not include your real name or any other personal information.
          Also, to avoid confusion on the scoreboard, you may not create a team that shares the same name as an existing user.</p>
          <form onSubmit={@onTeamJoin}>
            <Input type="text" valueLink={@linkState "team_name"} addonBefore={towerGlyph} label="Team Name" required/>
            <Input type="password" valueLink={@linkState "team_password"} addonBefore={lockGlyph} label="Team Password" required/>
            <Col md={6}>
              <span>
                <Button type="submit">Join Team</Button>
                <Button onClick={@onTeamRegistration}>Register Team</Button>
              </span>
            </Col>
          </form>
        </Panel>
    else
      <div/>

$ ->
  $("#password-update-form").on "submit", updatePassword
  $("#password-reset-form").on "submit", resetPassword
  $("#disable-account-form").on "submit", disableAccount

  React.render <TeamManagementForm/>, document.getElementById("team-management")
