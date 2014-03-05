module.exports = function(sequelize, DataTypes) {
  var User = sequelize.define('User', {
    username: DataTypes.STRING,
    passhash: DataTypes.STRING,
    token: DataTypes.STRING,    // this forces only one hash per user
    issuedDate: DataTypes.DATE  // since tokens are one way only, we need to make sure the token is valid for today
  }, {
    classMethods: {
    }
  });
 
  return User;
};
