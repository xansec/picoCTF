TabbedArea = ReactBootstrap.TabbedArea
TabPane = ReactBootstrap.TabPane

ManagementTabbedArea = React.createClass
  getInitialState: ->
    tab = window.location.hash.substring(1)
    if tab == ""
      tab = "problems"

    bundles: []
    problems: []
    submissions: []
    exceptions: []
    tabKey: tab

  onProblemChange: ->
    apiCall "GET", "http://localhost:5000/api/v1/problems?unlocked_only=false&include_disabled=true"
    .success ((data) ->
      @setState React.addons.update @state,
        problems: $set: data
    ).bind this
    .error (jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

    apiCall "GET", "http://localhost:5000/api/v1/bundles"
    .success ((data) ->
      @setState React.addons.update @state,
        bundles: $set: data
    ).bind this
    .error (jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

    #This could take awhile. However, it may
    #introduce a minor race condition with
    #get_all_problems
    apiCall "GET", "http://localhost:5000/api/v1/stats/submissions"
    .success ((data) ->
      @setState React.addons.update @state,
        submissions: $set: data
    ).bind this
    .error (jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

  onExceptionModification: ->
    apiCall "GET", "http://localhost:5000/api/v1/exceptions"
    .success ((data) ->
      @setState React.addons.update @state,
        exceptions: $set: data
    ).bind this
    .error (jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

  componentDidMount: ->
    # Formatting hack
    $("#main-content>.container").addClass("container-fluid")
    $("#main-content>.container").removeClass("container")

  componentWillMount: ->
    @onProblemChange()
    @onExceptionModification()

  onTabSelect: (tab) ->
    @setState React.addons.update @state,
      tabKey:
        $set: tab

    window.location.hash = "#"+tab

    if tab == "problems"
      @onProblemChange()

    if tab == "exceptions"
      @onExceptionModification()

  render: ->
      <TabbedArea activeKey={@state.tabKey} onSelect={@onTabSelect}>
        <TabPane eventKey='problems' tab='Manage Problems'>
          <ProblemTab problems={@state.problems} onProblemChange={@onProblemChange}
            bundles={@state.bundles} submissions={@state.submissions}/>
        </TabPane>
        <TabPane eventKey='exceptions' tab='Exceptions'>
          <ExceptionTab onExceptionModification={@onExceptionModification}
            exceptions={@state.exceptions}/>
        </TabPane>
        <TabPane eventKey='shell-servers' tab='Shell Server'>
          <ShellServerTab/>
        </TabPane>
        <TabPane eventKey='configuration' tab='Configuration'>
          <SettingsTab/>
        </TabPane>
      </TabbedArea>

$ ->
  React.render <ManagementTabbedArea/>, document.getElementById("management-tabs")
