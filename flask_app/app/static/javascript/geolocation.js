// jsで現在地の位置情報（緯度経度）を取得する。 by kouya

window.onload = function() {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(function(position) {
            post("/top", {latitude: position.coords.latitude, longitude: position.coords.longitude});
        });
    } else {
        alert("Geolocation is not supported by this browser.");
    }
};

// // 緯度経度の変数をFlaskへhttp経由のPOST形式で送信する。
// function sendLocationToServer(latitude, longitude) {
//     fetch('/top', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({latitude: latitude, longitude: longitude})
//     })
// }


/**
 * sends a request to the specified url from a form. this will change the window location.
 * @param {string} path the path to send the post request to
 * @param {object} params the parameters to add to the url
 * @param {string} [method=post] the method to use on the form
 */

function post(path, params, method='post') {

  // The rest of this code assumes you are not using a library.
  // It can be made less verbose if you use one.
  const form = document.createElement('form');
  form.method = method;
  form.action = path;

  for (const key in params) {
    if (params.hasOwnProperty(key)) {
      const hiddenField = document.createElement('input');
      hiddenField.type = 'hidden';
      hiddenField.name = key;
      hiddenField.value = params[key];

      form.appendChild(hiddenField);
    }
  }

  document.body.appendChild(form);
  form.submit();
}
