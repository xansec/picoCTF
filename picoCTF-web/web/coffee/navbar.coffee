userNotLoggedIn =
  News: "/news"

loggedInAdditions =
  Scoreboard: "/scoreboard"

teacherAdditions =
  Classroom: "/classroom"

adminAdditions =
  Management: "/management"

competitionAdditions =
  Problems: "/problems"
  Shell: "/shell"

loadNavbar = (renderNavbarLinks, renderNestedNavbarLinks) ->

  navbarLayout = {
    renderNavbarLinks: renderNavbarLinks,
    renderNestedNavbarLinks: renderNestedNavbarLinks
  }

  # Start out with the base links
  navbarLayout.links = userNotLoggedIn
  navbarLayout.topLevel = true

  # If a user is logged in, add status and links
  apiCall "GET", "http://localhost:5000/api/v1/user"
  .success ((data) ->
    navbarLayout.status = data
    if data.logged_in
      $.extend navbarLayout.links, loggedInAdditions
    else
      $(".show-when-logged-out").css("display", "inline-block")

    if data.teacher
      $.extend navbarLayout.links, teacherAdditions

    if data.admin
      $.extend navbarLayout.links, adminAdditions
    $("#navbar-links").html renderNavbarLinks(navbarLayout)
    $("#navbar-item-logout").on("click", logout)
  )

  # If a competition is active, add links
  apiCall "GET", "http://localhost:5000/api/v1/status"
  .success ((data) ->
    if data.competition_active
      $.extend navbarLayout.links, competitionAdditions
    $("#navbar-links").html renderNavbarLinks(navbarLayout)
    $("#navbar-item-logout").on("click", logout)
  )

  $("#navbar-links").html renderNavbarLinks(navbarLayout)
  $("#navbar-item-logout").on("click", logout)

$ ->
  renderNavbarLinks = _.template($("#navbar-links-template").remove().text())
  renderNestedNavbarLinks = _.template($("#navbar-links-dropdown-template").remove().text())

  loadNavbar(renderNavbarLinks, renderNestedNavbarLinks)
