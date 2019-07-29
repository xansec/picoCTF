window.apiCall = function(method, url, data, ga_event_class, ga_event) {
  const params = {
    method,
    url,
    dataType: "json",
    beforeSend(request) {
      request.setRequestHeader("X-CSRF-Token", $.cookie("token"));
    },
    timeout: 10000,
    error(jqXHR, textStatus, errorThrown) {
      // Notify for errors with no HTTP response code. Otherwise handle when calling @apiCall
      if (errorThrown === "") {
        ga("send", "event", "Error", "APIOffline", url);
        $.notify(
          "The server is currently down. We will work to fix this error right away.",
          "error"
        );
      } else {
        if (ga_event_class && ga_event) {
          ga(
            "send",
            "event",
            ga_event_class,
            ga_event,
            `Failure::${jqXHR.responseJSON.message}`
          );
        }
      }
    },
    success() {
      if (ga_event_class && ga_event) {
        ga("send", "event", ga_event_class, ga_event, "Success");
      }
    }
  };
  if (data) {
    params.data = JSON.stringify(data);
    params.contentType = "application/json";
  }
   return $.ajax(params);
};

window.redirectIfNotLoggedIn = () =>
  apiCall("GET", "/api/v1/user", null, "Redirect", "NotLoggedIn").success(
    function(data) {
      if (!data.logged_in) {
        window.location.href = "/";
      }
    }
  );

window.redirectIfLoggedIn = () =>
  apiCall("GET", "/api/v1/user", null, "Redirect", "LoggedIn").success(function(
    data
  ) {
    if (data.logged_in) {
      window.location.href = "/news";
    }
  });

window.redirectIfTeacher = () =>
  apiCall("GET", "/api/v1/user", null, "Redirect", "Teacher").success(function(
    data
  ) {
    if (data.teacher) {
      window.location.href = "/classroom";
    }
  });

window.redirectIfNotTeacher = () =>
  apiCall("GET", "/api/v1/user").success(function(data) {
    if (!data.teacher) {
      window.location.href = "/";
    }
  });

window.redirectIfNotAdmin = () =>
  apiCall("GET", "/api/v1/user", null, "Redirect", "Admin").success(function(
    data
  ) {
    if (!data.admin) {
      window.location.href = "/";
    }
  });

const getStyle = function(data) {
  let style = "info";
  switch (data.status) {
    case 0:
      style = "error";
      break;
    case 1:
      style = "success";
      break;
  }
  return style;
};

window.apiNotify = function(data, redirect) {
  const style = getStyle(data);
  $.notify(data.message, style);

  if (redirect && data.status === 1) {
    setTimeout(() => (window.location = redirect), 1000);
  }
};

window.apiNotifyElement = function(elt, data, redirect) {
  const style = getStyle(data);
  elt.notify(data.message, style);
  if (redirect && data.status === 1) {
    setTimeout(() => (window.location = redirect), 1000);
  }
};

window.numericalSort = data => data.sort((a, b) => b - a);

window.confirmDialog = function(
  message,
  title,
  yesButton,
  noButton,
  yesEvent,
  noEvent
) {
  const renderDialogModal = _.template($("#modal-template").html());
  const dialog_content = renderDialogModal({
    message,
    title,
    yesButton,
    noButton,
    submitButton: ""
  });
  $("#modal-holder").html(dialog_content);
  $("#confirm-modal")
    .modal({ backdrop: "static", keyboard: false })
    .one("click", "#modal-yes-button", yesEvent)
    .one("click", "#modal-no-button", noEvent);
};

window.messageDialog = function(message, title, button, event) {
  const renderDialogModal = _.template($("#modal-template").html());
  const dialog_content = renderDialogModal({
    message,
    title,
    yesButton: button,
    noButton: "",
    submitButton: ""
  });
  $("#modal-holder").html(dialog_content);
  $("#confirm-modal")
    .modal({ backdrop: "static", keyboard: false })
    .one("click", "#modal-yes-button", event);
};

window.formDialog = function(message, title, button, defaultFocus, event) {
  const renderDialogModal = _.template($("#modal-template").html());
  const dialog_content = renderDialogModal({
    message,
    title,
    yesButton: "",
    noButton: "",
    submitButton: button
  });
  $("#modal-holder").html(dialog_content);
   $("#confirm-modal")
    .modal({ backdrop: "static", keyboard: false })
    .on("shown.bs.modal", () => $(`#${defaultFocus}`).focus())
    .on("click", "#modal-submit-button", event);
};

window.closeDialog = () => $("#confirm-modal").modal("hide");

window.logout = () =>
  apiCall(
    "GET",
    "/api/v1/user/logout",
    null,
    "Authentication",
    "LogOut"
  ).success(data => (document.location.href = "/"));

$.fn.apiNotify = function(data, configuration) {
  configuration["className"] = getStyle(data);
  $(this).notify(data.message, configuration);
};

// Source: http://stackoverflow.com/a/17488875
$.fn.serializeObject = function() {
  const o = {};
  const a = this.serializeArray();
  $.each(a, function() {
    if (o[this.name]) {
      if (!o[this.name].push) {
        o[this.name] = [o[this.name]];
      }
      o[this.name].push(this.value || "");
    } else {
      (o[this.name] = this.value || "");
    }
  });
  return o;
};

$(() =>
  apiCall("GET", "/api/v1/user").success(
    data => (document.competition_status = data)
  )
);
