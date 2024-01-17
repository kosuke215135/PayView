// 以下PC版
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



//以下スマホ版
const user_picture_phone = document.getElementById('loginPopupButton_phone');
const popupContainer_phone = document.getElementById('loginpopupContainer_phone');

console.log(user_picture_phone)

var is_openPup_phone = false

// user_picture_phoneがクリックされたときの処理
user_picture_phone.addEventListener('click', function() {
    if (!is_openPup_phone){
        popupContainer_phone.style.display = 'block';
        is_openPup_phone = true;
    }else{
        popupContainer_phone.style.display = 'none';
        is_openPup_phone = false; 
    }
});


// ポップアップの外側がクリックされたときの処理
window.addEventListener('click', function(event) {
    if ((event.target !== popupContainer_phone) && (event.target !== user_picture_phone) && (is_openPup_phone)) {
        popupContainer_phone.style.display = 'none';
        is_openPup_phone = false;
    }
});
