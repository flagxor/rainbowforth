var HTTP = {};

HTTP._factories = [
  function() { return new XMLHttpRequest(); },
  function() { return new ActiveXObject('Msxml2.XMLHTTP'); },
  function() { return new ActiveXObject('Microsoft.XMLHTTP'); },
];

HTTP._factory = null;

HTTP.newRequest = function() {
  if (HTTP._factory != null) return HTTP._factory();
  for(var i = 0; i < HTTP._factories.length; i++) {
    try {
      var factory = HTTP._factories[i];
      var request = factory();
      if (request != null) {
        HTTP._factory = factory;
        return request;
      }
    } catch(e) {
      continue;
    }
  }
  HTTP._factory = function() {
    throw new Error('XMLHttpRequest not supported');
  }
  HTTP._factory();
};

HTTP.encodeFormData = function(data) {
  var pairs = [];
  var regexp = /%20/g;

  for (var name in data) {
    var value = data[name].toString();
    var pair = encodeURIComponent(name).replace(regexp, '+') + '=' +
               encodeURIComponent(value).replace(regexp, '+');
    pairs.push(pair);
  }

  return pairs.join('&');
};

HTTP.post = function(url, values, callback, errorHandler) {
  var request = HTTP.newRequest();
  request.onreadystatechange = function() {
    if (request.readyState == 4) {
      if (request.status == 200) {
        callback(request.responseText);
      } else {
        if (errorHandler != null) {
          errorHandler(request.status, request.statusText);
        } else {
          callback(null);
        }
      }
    }
  };
  request.open('POST', url);
  request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
  request.send(HTTP.encodeFormData(values));
};

HTTP.getText = function(url, callback) {
  var request = HTTP.newRequest();
  request.onreadystatechange = function() {
    if (request.readyState == 4) {
      if (request.status == 200) {
        callback(request.responseText);
      } else {
        callback(null);
      }
    }
  }
  request.open('GET', url);
  request.send(null);
};

