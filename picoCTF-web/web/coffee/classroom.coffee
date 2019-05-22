renderGroupInformation = _.template($("#group-info-template").remove().text())

renderTeamSelection = _.template($("#team-selection-template").remove().text())

@groupListCache = []

String.prototype.hashCode = ->
	hash = 0
	for i in [0...@length]
 		char = @charCodeAt i
 		hash = ((hash << 5) - hash) + char
 		hash = hash & hash
 	hash

@getName = (first, last, user) ->
  name = (first + " " + last).trim()
  if (name)
    name += " (" + user + ")"
  else
    name = user
  return name

createGroupSetup = () ->
    formDialogContents = _.template($("#new-group-template").html())({})
    formDialog formDialogContents, "Create a New Classroom", "OK", "new-group-name", () ->
        createGroup($('#new-group-name').val())

@exportProblemCSV = (groupName, teams) ->
  apiCall "GET", "http://localhost:5000/api/v1/problems?unlocked_only=false"
  .success (data) ->
    # problems = _.filter resp.data.problems, (problem) -> !problem.disabled
    problems = data; # non-admin API only returns non-disabled problems as top level data array
    outputData = [["Teamname", "Member Name(s)"].concat(_.map(problems, (problem) -> problem.name), ["Total"])]
    _.each teams, ((team) ->
      members = '"' + team.members.map((member) -> return this.getName(member.firstname, member.lastname, member.username)).join(", ") + '"'
      teamData = [team.team_name, members]
      teamData = teamData.concat _.map problems, ((problem) ->
        solved = _.find team.solved_problems, (solvedProblem) -> solvedProblem.name == problem.name
        return if solved then problem.score else 0
      )
      teamData = teamData.concat [team.score]
      outputData.push teamData
    )
    csvData = (_.map outputData, (fields) -> fields.join ",").join "\n"
    download(csvData, "#{groupName}.csv", "text/csv")
  .error (jqXHR) ->
    apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

loadGroupOverview = (groups, showFirstTab, callback) ->
  $("#group-overview").html renderGroupInformation({data: groups})

  $("#new-class-tab").on "click", (e) ->
    createGroupSetup()

  $("#new-class-button").on "click", (e) ->
    createGroupSetup()

  $("#class-tabs").on 'shown.bs.tab', 'a[data-toggle="tab"]', (e) ->
    tabBody = $(this).attr("href")
    groupName = $(this).data("group-name")

    apiCall "GET", "http://localhost:5000/api/v1/groups" + $(this).data("gid")
    .success (data) ->
        ga('send', 'event', 'Group', 'LoadTeacherGroupInformation', 'Success')
        for group in groups
          if `group.name == groupName` # coffee script will translate to === which doesn't work for numbers (e.g. 14741)
            $(tabBody).html renderTeamSelection({teams: data.members, groupName: groupName, owner: group.owner, gid: group.gid})
        $(".team-visualization-enabler").on "click", (e) ->
          tid = $(e.target).data("tid")
          for team in data.members
            if tid == team.tid
              preparedData = {status: 1, data: team.progression}
              window.renderTeamProgressionGraph("#visualizer-"+tid, preparedData)
              #hack
              _.delay window.renderTeamRadarGraph, 150, "#radar-visualizer-"+tid, tid

  if showFirstTab
    $('#class-tabs a:first').tab('show')


  $("ul.nav-tabs a").click ( (e) ->
    e.preventDefault();
    $(this).tab 'show'
  );

  $("#group-request-form").on "submit", groupRequest
  $(".delete-group-span").on "click", (e) ->
    deleteGroup $(e.target).data("gid")

  if callback
    callback()

loadGroupInfo = (showFirstTab, callback) ->
  apiCall "GET", "http://localhost:5000/api/v1/groups", null, 'Group', 'GroupListLoad'
  .success (data) ->
    window.groupListCache = data
    loadGroupOverview data, showFirstTab, callback
  .error (jqXHR) ->
    apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

createGroup = (groupName) ->
  data = {"name": groupName}
  apiCall "POST",  "http://localhost:5000/api/v1/groups", data, 'Group', 'CreateGroup'
  .success (data) ->
    closeDialog()
    apiNotify {"status": 1, "message": "Successfully created classroom."}
    loadGroupInfo(false, () ->
      $('#class-tabs li:eq(-2) a').tab('show'))
  .error (jqXHR) ->
    apiNotifyElement($("#new-group-name"), {"status": 0, "message": jqXHR.responseJSON.message})

deleteGroup = (gid) ->
  confirmDialog("You are about to permanently delete this class. This will automatically remove your students from this class. Are you sure you want to delete this class?",
                "Class Confirmation", "Delete Class", "Cancel",
                () ->
                  apiCall "DELETE", "http://localhost:5000/api/v1/groups" + gid, null, 'Group', 'DeleteGroup'
                  .success (data) ->
                    apiNotify {"status": 1, "message": "Successfully deleted classroom"}
                    loadGroupInfo(true)
               ,() ->
                  ga('send', 'event', 'Group', 'DeleteGroup', 'RejectPrompt'))

#Could be simplified without this function
groupRequest = (e) ->
  e.preventDefault()
  groupName = $("#group-name-input").val()
  createGroup groupName

$ ->
  if not window.userStatus
    apiCall "GET", "http://localhost:5000/api/v1/user"
    .success (data) ->
      window.userStatus = data
      if not window.userStatus.teacher
        apiNotify {status: 1, message: "You are no longer a teacher."}, "/profile"
  else if not window.userStatus.teacher
      apiNotify {status: 1, message: "You are no longer a teacher."}, "/profile"

  loadGroupInfo(true)

  $(document).on 'shown.bs.tab', 'a[href="#group-overview-tab"]', () ->
    loadGroupInfo(true)

  return
