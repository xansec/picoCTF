renderShellServers = _.template($("#shell-servers-template").remove().text())

$ ->
  apiCall "GET", "http://localhost:5000/api/v1/user/shell_servers"
  .success (data) ->
    if data.length > 0
      $("#shell-servers").html renderShellServers({servers: data})
  .error (jqXHR) ->
    apiNotify {"status": 0, "message": jqXHR.responseJSON.message}
