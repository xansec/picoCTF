Input = ReactBootstrap.Input
Row = ReactBootstrap.Row
Col = ReactBootstrap.Col
Button = ReactBootstrap.Button
Panel = ReactBootstrap.Panel
Glyphicon = ReactBootstrap.Glyphicon
ButtonInput = ReactBootstrap.ButtonInput
ButtonGroup = ReactBootstrap.ButtonGroup
Alert = ReactBootstrap.Alert

update = React.addons.update

Recaptcha = ReactRecaptcha

LoginForm = React.createClass

  render: ->
    userGlyph = <Glyphicon glyph="user"/>
    lockGlyph = <Glyphicon glyph="lock"/>

    formButton = if @props.status == "Login" then \

    q = "'" #My syntax highlighting can't handle literal quotes in jsx. :(
    if @props.status == "Reset"
      <Panel>
        <form onSubmit={@props.onPasswordReset}>
          <p><i>A password reset link will be sent the user{q}s email.</i></p>
          <Input type="text" name="username" valueLink={@props.username} addonBefore={userGlyph} placeholder="Username" required/>
          <div style={{height: "70px"}}/>
          <Row>
            <Col md={6}>
              <ButtonInput type="submit">Reset Password</ButtonInput>
            </Col>
            <Col md={6}>
              <span className="pull-right pad">Go back to <a onClick={@props.setPage.bind null, "Login"}>Login</a>.</span>
            </Col>
          </Row>
        </form>
      </Panel>
    else
      showGroupMessage = (->
        <Alert bsStyle="info">
          You are registering as a member of <strong>{@props.groupName}</strong>.
        </Alert>
      ).bind this

      showEmailFilter = (->
        <Alert bsStyle="warning">
          You can register provided you have an email for one of these domains: <strong>{@props.emailFilter.join ", "}</strong>.
        </Alert>
      ).bind this

      generateRecaptcha = ( ->
        if @props.reCAPTCHA_public_key
              <Recaptcha sitekey={@props.reCAPTCHA_public_key} verifyCallback={@props.onRecaptchaSuccess} expiredCallback={@props.onRecaptchaExpire} render="explicit"  />
      ).bind this

      # Toggle input fields according to user type
      showOrHide = ((prop, inputName) ->
        inputs = {
          firstname: false
          lastname: false
          url: false
          grade: false
          teacherlevel: false
          subjectstaught: false
          schoolcountry: false
          residencecountry: true
          affiliation: true
          zipcode: false
          studentOnly: false
          teacherOnly: false
          referrer: false
          gender: true
        }
        switch @props.usertype.value
          when "student"
            inputs.grade = true
            inputs.schoolcountry = true
            inputs.zipcode = true
            inputs.studentOnly = true
            inputs.referrer = true
            inputs.url = true
          when "college"
            inputs.schoolcountry = true
            inputs.zipcode = true
            inputs.url = true
          when "teacher"
            inputs.teacherlevel = true
            inputs.subjectstaught = true
            inputs.schoolcountry = true
            inputs.zipcode = true
            inputs.teacherOnly = true
            inputs.referrer = true
            inputs.url = true
          when "other"
            inputs.url = true
          else
            inputs.affiliation = false
        show = inputs[inputName]
        if prop == "class"
          if show then 'show' else 'hide'
        else if prop == "disabled"
          if show then false else true
      ).bind this

      generateCountries = ( ->
        countryList =
          "United States": "US"
          "Canada": "CA"
          "Afghanistan": "AF"
          "Albania": "AL"
          "Algeria": "DZ"
          "Andorra": "AD"
          "Angola": "AO"
          "Antigua and Barbuda": "AG"
          "Argentina": "AR"
          "Armenia": "AM"
          "Aruba": "AW"
          "Australia": "AU"
          "Austria": "AT"
          "Azerbaijan": "AZ"
          "Bahamas, The": "BS"
          "Bahrain": "BH"
          "Bangladesh": "BD"
          "Barbados": "BB"
          "Belarus": "BY"
          "Belgium": "BE"
          "Belize": "BZ"
          "Benin": "BJ"
          "Bhutan": "BT"
          "Bolivia": "BO"
          "Bosnia and Herzegovina": "BA"
          "Botswana": "BW"
          "Brazil": "BR"
          "Brunei": "BN"
          "Bulgaria": "BG"
          "Burkina Faso": "BF"
          "Burma": "MM"
          "Burundi": "BI"
          "Cabo Verde": "CV"
          "Cambodia": "KH"
          "Cameroon": "CM"
          "Central African Republic":"CF"
          "Chad": "TD"
          "Chile": "CL"
          "China": "CN"
          "Colombia": "CO"
          "Comoros": "KM"
          "Congo (Brazzaville)": "CG"
          "Congo (Kinshasa)": "CD"
          "Costa Rica": "CR"
          "Côte d'Ivoire": "CI"
          "Croatia": "HR"
          "Cuba": "CU"
          "Curacao": "CW"
          "Cyprus": "CY"
          "Czechia": "CZ"
          "Denmark": "DK"
          "Djibouti": "DJ"
          "Dominica": "DM"
          "Dominican Republic": "DO"
          "Ecuador": "EC"
          "Egypt": "EG"
          "El Salvador": "SV"
          "Equatorial Guinea": "GQ"
          "Eritrea": "ER"
          "Estonia": "EE"
          "Eswatini": "SZ"
          "Ethiopia": "ET"
          "Fiji": "FJ"
          "Finland": "FI"
          "France": "FR"
          "Gabon": "GA"
          "Gambia, The": "GM"
          "Georgia": "GE"
          "Germany": "DE"
          "Ghana": "GH"
          "Greece": "GR"
          "Grenada": "GD"
          "Guatemala": "GT"
          "Guinea": "GN"
          "Guinea-Bissau": "GW"
          "Guyana": "GY"
          "Haiti": "HT"
          "Holy See": "VA"
          "Honduras": "HN"
          "Hong Kong": "HK"
          "Hungary": "HU"
          "Iceland": "IS"
          "India": "IN"
          "Indonesia": "ID"
          "Iran": "IR"
          "Iraq": "IQ"
          "Ireland": "IE"
          "Israel": "IL"
          "Italy": "IT"
          "Jamaica": "JM"
          "Japan": "JP"
          "Jordan": "JO"
          "Kazakhstan": "KZ"
          "Kenya": "KE"
          "Kiribati": "KI"
          "Korea, North": "KP"
          "Korea, South": "KR"
          "Kosovo": "XK"
          "Kuwait": "KW"
          "Kyrgyzstan": "KG"
          "Laos": "LA"
          "Latvia": "LV"
          "Lebanon": "LB"
          "Lesotho": "LS"
          "Liberia": "LR"
          "Libya": "LY"
          "Liechtenstein": "LI"
          "Lithuania": "LT"
          "Luxembourg": "LU"
          "Macau": "MO"
          "Macedonia": "MK"
          "Madagascar": "MG"
          "Malawi": "MW"
          "Malaysia": "MY"
          "Maldives": "MV"
          "Mali": "ML"
          "Malta": "MT"
          "Marshall Islands": "MH"
          "Mauritania": "MR"
          "Mauritius": "MU"
          "Mexico": "MX"
          "Micronesia": "FM"
          "Moldova": "MD"
          "Monaco": "MC"
          "Mongolia": "MN"
          "Montenegro": "ME"
          "Morocco": "MA"
          "Mozambique": "MZ"
          "Namibia": "NA"
          "Nauru": "NR"
          "Nepal": "NP"
          "Netherlands": "NL"
          "New Zealand": "NZ"
          "Nicaragua": "NI"
          "Niger": "NE"
          "Nigeria": "NG"
          "Norway": "NO"
          "Oman": "OM"
          "Pakistan": "PK"
          "Palau": "PW"
          "Palestine": "PS"
          "Panama": "PA"
          "Papua New Guinea": "PG"
          "Paraguay": "PY"
          "Peru": "PE"
          "Philippines": "PH"
          "Poland": "PL"
          "Portugal": "PT"
          "Qatar": "QA"
          "Romania": "RO"
          "Russia": "RU"
          "Rwanda": "RW"
          "Saint Kitts and Nevis": "KN"
          "Saint Lucia": "LC"
          "Saint Vincent and the Grenadines": "VC"
          "Samoa": "WS"
          "San Marino": "SM"
          "Sao Tome and Principe": "ST"
          "Saudi Arabia": "SA"
          "Senegal": "SN"
          "Serbia": "RS"
          "Seychelles": "SC"
          "Sierra Leone": "SL"
          "Singapore": "SG"
          "Sint Maarten": "SX"
          "Slovakia": "SK"
          "Slovenia": "SI"
          "Solomon Islands": "SB"
          "Somalia": "SO"
          "South Africa": "ZA"
          "South Sudan": "SS"
          "Spain": "ES"
          "Sri Lanka": "LK"
          "Sudan": "SD"
          "Suriname": "SR"
          "Sweden": "SE"
          "Switzerland": "CH"
          "Syria": "SY"
          "Taiwan": "TW"
          "Tajikistan": "TJ"
          "Tanzania": "TZ"
          "Thailand": "TH"
          "Timor-Leste": "TL"
          "Togo": "TG"
          "Tonga": "TO"
          "Trinidad and Tobago": "TT"
          "Tunisia": "TN"
          "Turkey": "TR"
          "Turkmenistan": "TM"
          "Tuvalu": "TV"
          "Uganda": "UG"
          "Ukraine": "UA"
          "United Arab Emirates": "AE"
          "United Kingdom": "GB"
          "Uruguay": "UY"
          "Uzbekistan": "UZ"
          "Vanuatu": "VU"
          "Venezuela": "VE"
          "Vietnam": "VN"
          "Yemen": "YE"
          "Zambia": "ZM"
          "Zimbabwe": "ZW"

        for country, abbrev of countryList
          <option value=abbrev>{country}</option>
      )

      registrationForm = if @props.status == "Register" then \
        <div>
          <Row>
            <div>
              {if @props.groupName.length > 0 then showGroupMessage() else <span/>}
              {if @props.emailFilter.length > 0 and not @props.rid then showEmailFilter() else <span/>}
              <br/>
            </div>
            <Col md={6} className={showOrHide('class', 'firstname')}>
              <Input type="text" id="firstname" valueLink={@props.firstname} label="First Name" placeholder="Jane"/>
            </Col>
            <Col md={6} className={showOrHide('class', 'lastname')}>
              <Input type="text" id="lastname" valueLink={@props.lastname} label="Last Name" placeholder="Doe"/>
            </Col>
            <Col md={12}>
              <Input type="email" name="email" id="email" valueLink={@props.email} label="E-mail *" placeholder="email@example.com" required/>
            </Col>
          </Row>
          <Row>
            <Col md={12} className={showOrHide('class', 'residencecountry')}>
              <Input type="select" name="residencecountry" id="residencecountry" defaultValue="" valueLink={@props.residencecountry} label="Country/Region of Residence *" placeholder="Country of Residence" required>
              <option value="" disabled>-Select-</option>
              {generateCountries()}
              </Input>
            </Col>
          </Row>
          <Row>
            <Col md={12}>
              <Input type="select" name="usertype" id="usertype" defaultValue="" label="Status *" required valueLink={@props.usertype}>
                <option value="" disabled>-Select Category-</option>
                <option value="student">Middle/High School Student</option>
                <option value="teacher">Teacher/Instructor</option>
                <option value="college">College Student</option>
                <option value="other">Other</option>
              </Input>
            </Col>
          </Row>
          <Row>
            <Col md={6} className={showOrHide('class', 'affiliation')}>
              <Input type="text" name="affiliation" id="affiliation" valueLink={@props.affiliation} label={if @props.usertype.value == "other" then "Organization Name *" else "School Name *"} placeholder="Example School, Pittsburgh, PA" maxlength="50" required/>
            <p className="help-block">
               Your school or organization name may be visible to other users.
               </p>
            </Col>
            <Col md={6} className={showOrHide('class', 'url')}>
              <Input type="text" name="url" disabled={showOrHide( 'disabled', 'url')} id="url" valueLink={@props.url} label={if @props.usertype.value == "other" then "Organization URL (optional)" else "School URL (optional)"} placeholder={if @props.usertype.value == "other" then "Organization URL" else "School URL"}/>
            </Col>
          </Row>
          <Row>
            <Col md={6} className={showOrHide('class', 'grade')}>
              <Input type="number" min="1" max="12" name="grade" disabled={showOrHide('disabled','grade')} id="grade" valueLink={@props.grade} label="Your Current Grade/Year (1-12) *" placeholder="Your Current Grade/Year" required/>
            </Col>
            <Col md={6} className={showOrHide('class', 'teacherlevel')}>
              <label>I teach *</label>
              <Input type="checkbox" checkedLink={@props.teacher_middleschool} label="Middle School"/>
              <Input type="checkbox" checkedLink={@props.teacher_highschool} label="High School"/>
              <Input type="checkbox" checkedLink={@props.teacher_afterschoolclub} label="After School or Club"/>
              <Input type="checkbox" checkedLink={@props.teacher_homeschool} label="Home School"/>
            </Col>
            <Col md={6} className={showOrHide('class', 'subjectstaught')}>
              <Input type="text" name="subjectstaught" disabled={showOrHide('disabled', 'subjectstaught')} id="subjectstaught" valueLink={@props.subjectstaught} label="Subjects Taught *" required/>
            </Col>
          </Row>
          <Row>
            <Col md={6} className={showOrHide('class', 'zipcode')}>
              <Input type="text" name="zipcode" disabled={showOrHide('disabled','zipcode')}  id="zipcode" valueLink={@props.zipcode} label="School Zip Code/Postal Code *" placeholder="School Zipcode/Postal Code" required/>
            </Col>
            <Col md={6} className={showOrHide('class', 'schoolcountry')}>
              <Input type="select" name="schoolcountry" disabled={showOrHide('disabled','schoolcountry')} defaultValue="" id="schoolcountry" valueLink={@props.schoolcountry} label="School Country *" required>
              <option value="" disabled>-Select-</option>
              {generateCountries()}
              </Input>
            </Col>
          </Row>

          <Row className={showOrHide('class', 'referrer')}>
            <Col md={12}>
              <Input className={showOrHide('disabled', 'referrer')} type="select" name="referrer" defaultValue="" id="referrer" label="How did you hear about picoCTF?" valueLink={@props.referrer}>
                <option value="" disabled>-Select-</option>
                <option value="socialmedia">Social Media</option>
                <option className={showOrHide('class', 'studentOnly')} value="friends">Friends</option>
                <option <option className={showOrHide('class', 'studentOnly')} value="teacher">Teacher</option>
                <option <option className={showOrHide('class', 'teacherOnly')} value="students">Students</option>
                <option <option className={showOrHide('class', 'teacherOnly')} value="colleagues_groupemail">Colleagues or group email</option>
              </Input>
            </Col>
          </Row>
          <Row className={showOrHide('class', 'gender')}>
            <Col md={12}>
              <Input type="select" id="gender" name="gender" defaultValue="" label="Which gender identity do you most identify with?" valueLink={@props.gender}>
                  <option value="">-Select-</option>
                  <option value="woman">Woman</option>
                  <option value="man">Man</option>
                  <option value="transgenderwoman">Transgender Woman</option>
                  <option value="transgenderman">Transgender Man</option>
                  <option value="gfnc">Gender Fluid/Non-Conforming</option>
              </Input>
            </Col>
          </Row>
          <Row>
            <Col md={12}>
             <Input type="select" name="age" id="age" defaultValue="" label="What is your age? *" valueLink={@props.age} required>
                  <option value="">-Select-</option>
                  <option value="13-17">I am between 13 and 17 years of age</option>
                  <option value="18+">I am 18 years of age or older</option>
              </Input>
            </Col>
          </Row>
          <Row className={if @props.age.value == "13-17" then "show" else "hide"}>
            <Col md={12}>
              <p className="help-block">
               Parent or legal guardian must insert contact email address.  By inserting email address and finalizing
               registration, parent/legal guardian is hereby consenting to their child’s registration under the Terms of
                Use, Privacy Statement and any applicable Competition Rules.
               </p>
              <Input type="email" name="parentemail" disabled={if @props.age.value == "13-17" then false else true} id="parentemail" valueLink={@props.parentemail} label="Parent's E-mail *" required placeholder="email@example.com" />
            </Col>
          </Row>
          <Row>
            <Col md={8}>
              {generateRecaptcha()}
             </Col>
            <Col md={4} className="text-right">
              <ButtonInput className="btn-primary" type="submit">Register</ButtonInput>
            </Col>
          </Row>
        </div> else <span/>
      <Panel>
        <form key={@props.status} onSubmit={if @props.status == "Login" then @props.onLogin else @props.onRegistration}>
          <Input type="text" id="username" valueLink={@props.username} addonBefore={userGlyph} label="Username" required/>
          <p className={if @props.status == "Login" then "hide" else "help-block"}>Your username may be visible to other users.
          Do not include your real name or any other personal information.</p>
          <Input type="password" id="password" valueLink={@props.password} addonBefore={lockGlyph} label="Password" required/>
          <Row>
            <Col md={6}>
              {if @props.status == "Register" then \
                <span className="pad">Go back to <a onClick={@props.setPage.bind null, "Login"}>Login</a>.</span>
              else <span>
                <Button type="submit">Login</Button>
                <Button id="set-register" onClick={@props.setPage.bind null, "Register"}>Register</Button>
              </span>}
            </Col>
            <Col md={6}>
              <a className="pad" onClick={@props.setPage.bind null, "Reset"}>Need to reset your password?</a>
            </Col>
          </Row>
          {registrationForm}
        </form>
      </Panel>


TeamManagementForm = React.createClass
  mixins: [React.addons.LinkedStateMixin]

  getInitialState: ->
    team_name: ""
    team_password: ""

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

  render: ->

    towerGlyph = <Glyphicon glyph="tower"/>
    lockGlyph = <Glyphicon glyph="lock"/>

    <Panel>
      <p>Your team name may be visible to other users. Do not include your real name or any other personal information.
        Also, to avoid confusion on the scoreboard, you may not create a team that shares the same name as an existing user.</p>
      <form onSubmit={@onTeamJoin}>
        <Input type="text" valueLink={@linkState "team_name"} addonBefore={towerGlyph} label="Team Name" required/>
        <Input type="password" valueLink={@linkState "team_password"} addonBefore={lockGlyph} label="Team Password" required/>
        <Col md={6}>
          <span> <Button type="submit">Join Team</Button>
            <Button onClick={@onTeamRegistration}>Register Team</Button>
          </span>
        </Col>
        <Col md={6}>
          <a href="#" onClick={() -> document.location.href = "/profile"}>Play as an individual.</a>
        </Col>
      </form>
    </Panel>

AuthPanel = React.createClass
  mixins: [React.addons.LinkedStateMixin]
  getInitialState: ->
    params = $.deparam $.param.fragment()

    page: "Login"
    settings: {}
    gid: params.g
    rid: params.r
    status: params.status
    groupName: ""
    captcha: ""
    regStats: {}

  componentWillMount: ->
    if @state.status == "verified"
      apiNotify({status: 1, message: "Your account has been successfully verified. Please login."})
    else if @state.status == "verification_error"
      apiNotify({status: 0, message: "Invalid verification code. Please contact an administrator."})
    if @state.gid
      apiCall "GET", "/api/v1/groups/" + @state.gid
      .success ((data) ->
        @setState update @state,
          groupName: $set: data.name
          affiliation: $set: data.name
          settings: $merge: data.settings
          page: $set: "Register"
      ).bind this
    else
      apiCall "GET", "/api/v1/status"
      .success ((data) ->
        @setState update @state,
          settings: $merge: data
      ).bind this

    apiCall "GET", "/api/v1/user"
    .success ((data) ->
      @setState update @state,
        settings: $merge: data
    ).bind this

    apiCall "GET", "/api/v1/stats/registration"
    .success ((data) ->
      @setState update @state,
        regStats: $set: data
    ).bind this

  onRegistration: (e) ->
    e.preventDefault()

    if @state.settings.enable_captcha && @state.captcha == ""
      apiNotify {status: 0, message: "ReCAPTCHA required."}
      return

    form = {}
    form.gid = @state.gid
    form.rid = @state.rid
    form.username = @state.username
    form.password = @state.password
    form.firstname = @state.firstname
    form.lastname = @state.lastname
    form.email = @state.email
    form.affiliation = @state.affiliation
    form.usertype = @state.usertype
    form.demo = {}

    for k,v of @state
      if k.substr(0,5) == "demo_"
        form.demo[k.substr(5)] = v

    if @state.usertype in ["student", "teacher"]
      form.country = form.demo.schoolcountry
    else
      form.country = form.demo.residencecountry

    form['g-recaptcha-response'] = @state.captcha

    apiCall "POST", "/api/v1/users", form
    .success ((data) ->
      verificationAlert =
        status: 1
        message: "You have been sent a verification email. You will need to complete this step before logging in."

      successAlert =
        status: 1
        message: "User " + @state.username + " registered successfully!"

      if @state.settings.email_verification and not @state.rid
        apiNotify verificationAlert
        @setPage "Login"
        if @state.settings.max_team_size > 1
          document.location.hash = "#team-builder"
      else
        apiCall "POST", "/api/v1/user/login", {"username": @state.username, "password": @state.password}
        .success ((loginData) ->
          apiCall "GET", "/api/v1/user"
          .success ((userData) ->
            if data.teacher
              apiNotify successAlert, "/profile"
            else if @state.settings.max_team_size > 1
              apiNotify successAlert
              @setPage "Team Management"
            else
              apiNotify successAlert, "/profile"
          ).bind this
          .error (jqXHR) ->
            apiNotify {"status": 0, "message": jqXHR.responseJSON.message}
        ).bind this
        .error (jqXHR) ->
          apiNotify {"status": 0, "message": jqXHR.responseJSON.message}
    ).bind this
    .error (jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

  onPasswordReset: (e) ->
    e.preventDefault()
    apiCall "POST", "/api/v1/user/reset_password/request", {username: @state.username}
    .success ((resp) ->
      apiNotify {status: 1, message: "A password reset link has been sent to the email address provided during registration."}
      @setPage "Login"
    ).bind this
    .error (jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

  onLogin: (e) ->
    e.preventDefault()
    apiCall "POST", "/api/v1/user/login", {username: @state.username, password: @state.password}
    .success ->
      # Get teacher status
      apiCall "GET", "/api/v1/user"
      .success ((data) ->
        if document.location.hash == "#team-builder" and not data.teacher
          @setPage "Team Management"
        else
          if data.teacher
            document.location.href = "/classroom"
          else
            document.location.href = "/profile"
      )
    .error (jqXHR) ->
      apiNotify {"status": 0, "message": jqXHR.responseJSON.message}

  setPage: (page) ->
    @setState update @state,
        page: $set: page

  onRecaptchaSuccess: (captcha) ->
    @setState update @state,
      captcha: $set: captcha

  onRecaptchaExpire: () ->
    @setState update @state,
      captcha: $set: ""

  render: ->
    links =
    username: @linkState "username"
    password: @linkState "password"
    lastname: @linkState "lastname"
    firstname: @linkState "firstname"
    email: @linkState "email"
    affiliation: @linkState "affiliation"
    usertype: @linkState "usertype"
    age: @linkState "demo_age"
    url: @linkState "demo_url"
    residencecountry: @linkState "demo_residencecountry"
    schoolcountry: @linkState "demo_schoolcountry"
    zipcode: @linkState "demo_zipcode"
    grade: @linkState "demo_grade"
    referrer: @linkState "demo_referrer"
    gender: @linkState "demo_gender"
    teacher_middleschool: @linkState "demo_teacher_middleschool"
    teacher_highschool: @linkState "demo_teacher_highscool"
    teacher_afterschoolclub: @linkState "demo_teacher_afterschool"
    teacher_homeschool: @linkState "demo_teacher_homeschool"
    subjectstaught: @linkState "demo_subjectstaught"
    parentemail: @linkState "demo_parentemail"

    showRegStats = (()->
      if @state.regStats
        <Panel>
          <h4><strong>Registration Statistics</strong></h4>
          <p>
            <strong>{@state.regStats.users}</strong> users have registered, <strong>{@state.regStats.teamed_users}</strong> of
            which have formed <strong>{@state.regStats.teams}</strong> teams.<br />
            <strong>{@state.regStats.groups}</strong> classrooms have been created by teachers.
          </p>
        </Panel>
    ).bind this

    if @state.page == "Team Management"
      <div>
        <Row>
          <Col md={6} mdOffset={3}>
            <TeamManagementForm/>
          </Col>
        </Row>
      </div>
    else
      <div>
        <Row>
            <Col md={6} mdOffset={3}>
              <LoginForm setPage={@setPage} onRecaptchaSuccess={@onRecaptchaSuccess} onRecaptchaExpire={@onRecaptchaExpire}
                status={@state.page} reCAPTCHA_public_key={@state.settings.reCAPTCHA_public_key}
                onRegistration={@onRegistration} onLogin={@onLogin} onPasswordReset={@onPasswordReset}
                emailFilter={@state.settings.email_filter} groupName={@state.groupName} rid={@state.rid}
                gid={@state.gid} {...links}/>
              {showRegStats()}
            </Col>
        </Row>
      </div>

$ ->
  redirectIfLoggedIn()
  React.render <AuthPanel/>, document.getElementById("auth-box")
