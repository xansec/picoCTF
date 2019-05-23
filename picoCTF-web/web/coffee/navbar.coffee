apiOffline =
  News: "/news"

teacherLoggedIn =
  Problems: "/problems"
  Shell: "/shell"
  Scoreboard: "/scoreboard"
  Classroom: "/classroom"
  News: "/news"

teacherLoggedInNoCompetition =
  Scoreboard: "/scoreboard"
  Classroom: "/classroom"
  News: "/news"

userLoggedIn =
  Problems: "/problems"
  Shell: "/shell"
  Scoreboard: "/scoreboard"
  News: "/news"

userLoggedInNoCompetition =
  Scoreboard: "/scoreboard"
  News: "/news"

userNotLoggedIn =
  News: "/news"

adminLoggedIn =
  Management: "/management"

loadNavbar = (renderNavbarLinks, renderNestedNavbarLinks) ->

  navbarLayout = {
    renderNavbarLinks: renderNavbarLinks,
    renderNestedNavbarLinks: renderNestedNavbarLinks
  }

  apiCall "GET", "http://localhost:5000/api/v1/user"
  .success (userData) ->
    apiCall "GET", "http://localhost:5000/api/v1/status"
    .success (competitionData) ->
      navbarLayout.links = userNotLoggedIn
      navbarLayout.status = userData
      navbarLayout.topLevel = true
      if userData["logged_in"]
        if userData["teacher"]
          if competitionData["competition_active"]
            navbarLayout.links = teacherLoggedIn
          else
            navbarLayout.links = teacherLoggedInNoCompetition
        else
          if competitionData["competition_active"]
              navbarLayout.links = userLoggedIn
          else
              navbarLayout.links = userLoggedInNoCompetition
        if userData["admin"]
          $.extend navbarLayout.links, adminLoggedIn
      else
        $(".show-when-logged-out").css("display", "inline-block")
      $("#navbar-links").html renderNavbarLinks(navbarLayout)
      $("#navbar-item-logout").on("click", logout)
    .fail ->
      navbarLayout.links = apiOffline
      $("#navbar-links").html renderNavbarLinks(navbarLayout)
  .fail ->
    navbarLayout.links = apiOffline
    $("#navbar-links").html renderNavbarLinks(navbarLayout)

$ ->
  renderNavbarLinks = _.template($("#navbar-links-template").remove().text())
  renderNestedNavbarLinks = _.template($("#navbar-links-dropdown-template").remove().text())

  loadNavbar(renderNavbarLinks, renderNestedNavbarLinks)
