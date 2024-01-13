// jsで現在地の位置情報（緯度経度）を取得する。 by kouya

function post_position(path, to_url) {
  if ("geolocation" in navigator) {
      console.log("execute post_position")
      console.log(to_url)
      navigator.geolocation.getCurrentPosition(
        // 成功時のコールバック関数
        function(position) {
          post(path, {latitude: position.coords.latitude, longitude: position.coords.longitude, redirect_url: to_url});
        },
        // 失敗時のコールバック関数
        function(error) {
          // エラーメッセージを表示するか、適切な処理を行う
          console.error("位置情報の取得に失敗しました:", error.message);
          window.alert('位置情報をオンにしてください')
        }
      );
  } else {
    alert("Geolocation is not supported by this browser.");
  }
};

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


