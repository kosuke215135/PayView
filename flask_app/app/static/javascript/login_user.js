// ユーザー画像とポップアップ要素の取得
const user_picture = document.getElementById('loginPopupButton');
const popupContainer = document.getElementById('loginpopupContainer');

console.log(user_picture)

var is_openPup = false

// user_pictureがクリックされたときの処理
user_picture.addEventListener('click', function() {
    if (!is_openPup){
        popupContainer.style.display = 'block';
        is_openPup = true;
    }else{
        popupContainer.style.display = 'none';
        is_openPup = false; 
    }
});

// ポップアップの外側がクリックされたときの処理
window.addEventListener('click', function(event) {
    if ((event.target !== popupContainer) && (event.target !== user_picture) && (is_openPup)) {
        popupContainer.style.display = 'none';
        is_openPup = false;
    }
});
