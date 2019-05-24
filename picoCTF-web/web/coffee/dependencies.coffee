@apiCall = (method, url, data, ga_event_class, ga_event) ->
  params = {
    method: method,
    url: url,
    dataType: "json",
    beforeSend: (request) ->
      request.setRequestHeader "X-CSRF-Token", $.cookie("token")
    timeout: 10000,
    error: (jqXHR, textStatus, errorThrown) ->
      # Notify for errors with no HTTP response code. Otherwise handle when calling @apiCall
      if errorThrown == ""
        ga('send', 'event', 'Error', 'APIOffline', url)
        $.notify "The server is currently down. We will work to fix this error right away.", "error"
      else
        if ga_event_class and ga_event
          ga('send', 'event', ga_event_class, ga_event, "Failure::" + jqXHR.responseJSON.message)
    success: ->
      if ga_event_class and ga_event
          ga('send', 'event', ga_event_class, ga_event, "Success")
    }
  if data
    params.data = JSON.stringify(data)
    params.contentType = "application/json"
  $.ajax params


@redirectIfNotLoggedIn = ->
  apiCall "GET", "/api/v1/user", null, 'Redirect', 'NotLoggedIn'
  .success (data) ->
    if not data.logged_in
      window.location.href = "/"

@redirectIfLoggedIn = ->
  apiCall "GET", "/api/v1/user", null, 'Redirect', 'LoggedIn'
  .success (data) ->
    if data.logged_in
      window.location.href = "/news"

@redirectIfTeacher = ->
  apiCall "GET", "/api/v1/user", null, 'Redirect', 'Teacher'
  .success (data) ->
    if data.teacher
      window.location.href = "/classroom"

@redirectIfNotTeacher = ->
  apiCall "GET", "/api/v1/user"
  .success (data) ->
    if not data.teacher
      window.location.href = "/"

@redirectIfNotAdmin = ->
  apiCall "GET", "/api/v1/user", null, 'Redirect', 'Admin'
  .success (data) ->
    if not data.admin
      window.location.href = "/"

getStyle = (data) ->
  style = "info"
  switch data.status
    when 0
      style = "error"
    when 1
      style = "success"
  return style

@apiNotify = (data, redirect) ->
  style = getStyle data
  $.notify data.message, style

  if redirect and data.status is 1
    setTimeout (->
        window.location = redirect
      ), 1000

@apiNotifyElement = (elt, data, redirect) ->
  style = getStyle data
  elt.notify data.message, style
  if redirect and data.status is 1
    setTimeout (->
        window.location = redirect
      ), 1000

@numericalSort = (data) ->
  data.sort (a, b) ->
    return (b - a)

@confirmDialog = (message, title, yesButton, noButton, yesEvent, noEvent) ->
    renderDialogModal = _.template($("#modal-template").html())
    dialog_content = renderDialogModal({message: message, title: title, yesButton: yesButton, noButton: noButton, submitButton: ""})
    $("#modal-holder").html dialog_content
    $("#confirm-modal").modal {backdrop: "static", keyboard: false}
    .one "click", "#modal-yes-button", yesEvent
    .one "click", "#modal-no-button", noEvent

@messageDialog = (message, title, button, event) ->
    renderDialogModal = _.template($("#modal-template").html())
    dialog_content = renderDialogModal({message: message, title: title, yesButton: button, noButton: "", submitButton: ""})
    $("#modal-holder").html dialog_content
    $("#confirm-modal").modal {backdrop: "static", keyboard: false}
    .one "click", "#modal-yes-button", event

@formDialog = (message, title, button, defaultFocus, event) ->
    renderDialogModal = _.template($("#modal-template").html())
    dialog_content = renderDialogModal({message: message, title: title, yesButton: "", noButton: "", submitButton: button})
    $("#modal-holder").html dialog_content
    $("#confirm-modal").modal {backdrop: "static", keyboard: false}
    .on 'shown.bs.modal', () -> $("#" + defaultFocus).focus()
    .on "click", "#modal-submit-button", event

@closeDialog = () ->
    $('#confirm-modal').modal('hide')

@logout = ->
  apiCall "GET", "/api/v1/user/logout", null, 'Authentication', 'LogOut'
  .success (data) ->
    document.location.href = "/"

$.fn.apiNotify = (data, configuration) ->
  configuration["className"] = getStyle data
  return $(this).notify(data.message, configuration)

# Source: http://stackoverflow.com/a/17488875
$.fn.serializeObject = ->
   o = {}
   a = this.serializeArray()
   $.each(a, ->
       if o[this.name]
           if !o[this.name].push
               o[this.name] = [o[this.name]]
           o[this.name].push(this.value || '')
       else
           o[this.name] = this.value || ''
   )
   return o

$ ->
  apiCall "GET", "/api/v1/user"
  .success (data) ->
    document.competition_status = data


