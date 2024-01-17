// 以下PC版
// ユーザー画像とポップアップ要素の取得
const add_plus = document.getElementById('addPopupButton');
const add_popupContainer = document.getElementById('addpopupContainer');

console.log(add_plus)

var is_add_openPup = false

// add_plusがクリックされたときの処理
add_plus.addEventListener('click', function() {
    if (!is_add_openPup){
        add_popupContainer.style.display = 'block';
        is_add_openPup = true;
    }else{
        add_popupContainer.style.display = 'none';
        is_add_openPup = false; 
    }
});

// ポップアップの外側がクリックされたときの処理
window.addEventListener('click', function(event) {
    if ((event.target !== add_popupContainer) && (event.target !== add_plus) && (is_add_openPup)) {
        add_popupContainer.style.display = 'none';
        is_add_openPup = false;
    }
});

const add_shop_Popup = document.getElementById('add_shop_Popup');

function open_add_shop_Popup(){
    add_shop_Popup.style.display = 'block';
}

function close_add_shop_Popup(){
    add_shop_Popup.style.display = 'none';
}


