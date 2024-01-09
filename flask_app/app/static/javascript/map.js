function initMap() {
    // 地図の中心を設定
    var center = {lat: -34.397, lng: 150.644};

    // 地図を表示
    var map = new google.maps.Map(document.getElementById('map'), {
        zoom: 8,
        center: center
    });

    // マーカーを配置する位置の配列
    var locations = [
        {lat: -34.397, lng: 150.644},
        {lat: -34.490, lng: 150.744},
        {lat: -34.280, lng: 150.855}
    ];

    // 各位置にマーカーを配置
    locations.forEach(function(location) {
        var marker = new google.maps.Marker({
            position: location,
            map: map
        });
    });
}