// jsで現在地の位置情報（緯度経度）を取得する。 by kouya

window.onload = function() {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(function(position) {
            sendLocationToServer(position.coords.latitude, position.coords.longitude);
        });
    } else {
        alert("Geolocation is not supported by this browser.");
    }
};

// 緯度経度の変数をFlaskへhttp経由のPOST形式で送信する。
function sendLocationToServer(latitude, longitude) {
    fetch('/send-location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({latitude: latitude, longitude: longitude})
    })
}