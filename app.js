var express = require('express');
var http = require('http');
var path = require('path');
var favicon = require('static-favicon');
var logger = require('morgan');
var bodyParser = require('body-parser');

var routes = require('./routes');
var users = require('./routes/user');

var db = require('./models');

var app = express();

app.use(favicon());
app.use(logger('dev'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded());
// app.use(cookieParser());
app.use(app.router);

/// catch 404 and forwarding to error handler
app.use(function(req, res, next) {
    var err = new Error('Not Found');
    err.status = 404;
    next(err);
});

/// error handlers

// development error handler
// will print stacktrace
if (app.get('env') === 'development') {
    app.use(function(err, req, res, next) {
        res.render('error', {
            message: err.message,
            error: err
        });
    });
}

// production error handler
// no stacktraces leaked to user
app.use(function(err, req, res, next) {
    res.render('error', {
        message: err.message,
        error: {}
    });
});

module.exports = app;

// routes
app.get('/', routes.index);

// database and start up
db
  .sequelize
  .sync({ force: true })
  .complete(function (err) {
    if (err) {
      throw err;
    }

    port = app.get('port') || 3000;

    http.createServer(app).listen(port, function () {
      console.log('Express server listening on port ' + port);
    });
  });
